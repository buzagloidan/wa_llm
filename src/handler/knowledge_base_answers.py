import logging
from typing import List

from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from sqlmodel import select, cast, String, desc
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    before_sleep_log,
)

from models import Message, KBTopic
from whatsapp.jid import parse_jid
from utils.chat_text import chat2text
from utils.voyage_embed_text import voyage_embed_text
from .base_handler import BaseHandler

# Creating an object
logger = logging.getLogger(__name__)


class KnowledgeBaseAnswers(BaseHandler):
    async def __call__(self, message: Message):
        # Ensure message.text is not None before passing to generation_agent
        if message.text is None:
            logger.warning(f"Received message with no text from {message.sender_jid}")
            return
        # get the last 7 messages
        stmt = (
            select(Message)
            .where(Message.chat_jid == message.chat_jid)
            .order_by(desc(Message.timestamp))
            .limit(7)
        )
        res = await self.session.exec(stmt)
        history: list[Message] = list(res.all())

        rephrased_response = await self.rephrasing_agent(
            (await self.whatsapp.get_my_jid()).user, message, history
        )
        # Get query embedding
        embedded_question = (
            await voyage_embed_text(self.embedding_client, [rephrased_response.output])
        )[0]

        # Search company documentation for relevant topics
        limit_topics = 10
        cosine_distance_threshold = 0.7  # Threshold for considering a topic relevant
        
        # query for user query
        q = (
            select(
                KBTopic,
                KBTopic.embedding.cosine_distance(embedded_question).label(
                    "cosine_distance"
                ),
            )
            .order_by(KBTopic.embedding.cosine_distance(embedded_question))
            .where(KBTopic.embedding.cosine_distance(embedded_question) < cosine_distance_threshold)
            .limit(limit_topics)
        )
        retrieved_topics = await self.session.exec(q)

        similar_topics = []
        similar_topics_distances = []
        has_relevant_docs = False
        
        for kb_topic, topic_distance in retrieved_topics:  # Unpack the tuple
            similar_topics.append(f"{kb_topic.subject} \n {kb_topic.content}")
            similar_topics_distances.append(f"topic_distance: {topic_distance}")
            if topic_distance < 0.5:  # High relevance threshold
                has_relevant_docs = True

        sender_number = parse_jid(message.sender_jid).user
        generation_response = await self.generation_agent(
            message.text, similar_topics, message.sender_jid, history, has_relevant_docs
        )
        logger.info(
            "RAG Query Results:\n"
            f"Sender: {sender_number}\n"
            f"Question: {message.text}\n"
            f"Rephrased Question: {rephrased_response.output}\n"
            f"Chat JID: {message.chat_jid}\n"
            f"Retrieved Topics: {len(similar_topics)}\n"
            f"Similarity Scores: {similar_topics_distances}\n"
            "Topics:\n"
            + "\n".join(f"- {topic[:100]}..." for topic in similar_topics)
            + "\n"
            f"Generated Response: {generation_response.output}"
        )

        await self.send_message(
            message.chat_jid,
            generation_response.output,
        )
        
        # Send completion emoji reaction to indicate processing is done
        try:
            await self.whatsapp.react_to_message(
                message_id=message.message_id,
                phone=message.chat_jid,
                emoji="✅"
            )
            logger.info(f"Sent completion reaction ✅ for message {message.message_id}")
        except Exception as e:
            logger.warning(f"Failed to send completion reaction: {e}")

    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(6),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def generation_agent(
        self, query: str, topics: list[str], sender: str, history: List[Message], has_relevant_docs: bool = False
    ) -> AgentRunResult[str]:
        # Create dynamic system prompt based on whether we have relevant documentation
        if has_relevant_docs and topics:
            system_prompt = """
            You are a helpful and knowledgeable representative of Jeen.ai, a cutting-edge AI platform company.
            Your role is to assist enterprise employees with questions about how to use the Jeen.ai platform.
            
            IMPORTANT: You have access to highly relevant company documentation below. Use this information to provide accurate responses.
            
            Key guidelines:
            - Base your response primarily on the provided documentation
            - Be professional, friendly, and helpful
            - Keep responses CONCISE and to the point - avoid unnecessary details
            - Provide only essential information that directly answers the question
            - Answer in the same language as the user's query
            - Use short, clear sentences
            
            FORMATTING RULES FOR WHATSAPP:
            - DO NOT use markdown formatting (no *, #, **, etc.)
            - Use plain text with proper spacing and line breaks
            - Use simple bullet points with • or - if needed
            - Make text clean and easy to read on mobile
            - Use CAPITAL LETTERS sparingly for emphasis
            - Keep paragraphs short and well-spaced
            - Aim for brief, direct responses
            
            The documentation provided is highly relevant to the user's question - use it to give a focused, concise answer.
            """
        else:
            system_prompt = """
            You are a helpful and knowledgeable representative of Jeen.ai, a cutting-edge AI platform company.
            Your role is to assist enterprise employees with general questions about Jeen.ai.
            
            IMPORTANT: No highly relevant documentation was found for this specific query, so provide brief, general helpful responses.
            
            Key guidelines:
            - Be professional, friendly, and helpful
            - Keep responses SHORT and CONCISE
            - Provide only essential general information about Jeen.ai
            - If you don't have specific information, acknowledge this briefly
            - Offer to connect them with support in one simple sentence
            - Answer in the same language as the user's query
            - Avoid lengthy explanations
            
            FORMATTING RULES FOR WHATSAPP:
            - DO NOT use markdown formatting (no *, #, **, etc.)
            - Use plain text with proper spacing and line breaks
            - Use simple bullet points with • or - if needed
            - Make text clean and easy to read on mobile
            - Use CAPITAL LETTERS sparingly for emphasis
            - Keep paragraphs short and well-spaced
            - Aim for brief, direct responses
            
            Since no highly relevant documentation was found, be helpful but keep responses concise and direct.
            """

        agent = Agent(
            model="gemini-2.5-flash",
            system_prompt=system_prompt,
            )

        if has_relevant_docs and topics:
            prompt_template = f"""
            User Query: {query}
            
            # Recent chat history:
            {chat2text(history)}
            
            # Highly Relevant Jeen.ai Documentation:
            {"\n---\n".join(topics)}
            
            The above documentation is highly relevant to the user's question. Use it to provide a comprehensive, accurate response.
            """
        else:
            prompt_template = f"""
            User Query: {query}
            
            # Recent chat history:
            {chat2text(history)}
            
            # Available Documentation:
            {"\n---\n".join(topics) if len(topics) > 0 else "No highly relevant documentation found for this specific query."}
            
            Note: The available documentation may not be highly relevant to this specific question. Provide general Jeen.ai information and suggest appropriate resources.
            """

        return await agent.run(prompt_template)

    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(6),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def rephrasing_agent(
        self, my_jid: str, message: Message, history: List[Message]
    ) -> AgentRunResult[str]:
        rephrased_agent = Agent(
            model="gemini-2.5-flash",
            system_prompt=f"""Rephrase the following user message as a clear, concise search query for finding relevant Jeen.ai company documentation.
            - Use English only!
            - Focus on the core question or information need from the user
            - Convert conversational language into a structured query suitable for knowledge base search
            - Use the chat history for context if relevant, but focus on the main query
            - Return only the rephrased search query, no additional text!""",
        )

        # We obviously need to translate the question and turn the question vebality to a title / summary text to make it closer to the questions in the rag
        return await rephrased_agent.run(
            f"{message.text}\n\n## Recent chat history:\n {chat2text(history)}"
        )
