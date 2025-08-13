#!/usr/bin/env python3
"""
HTML dashboard for visualizing company documentation and topics
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from .deps import get_db_async_session

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_html(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_async_session)]
) -> HTMLResponse:
    """Serve HTML dashboard for viewing topics."""
    
    base_url = str(request.base_url).rstrip('/')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jeen.ai Documentation Dashboard</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: #3498db;
                color: white;
                padding: 20px;
                border-radius: 6px;
                text-align: center;
            }}
            .stat-card h3 {{
                margin: 0 0 10px 0;
                font-size: 2em;
            }}
            .controls {{
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                align-items: center;
            }}
            .controls input, .controls select, .controls button {{
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .controls button {{
                background: #3498db;
                color: white;
                border: none;
                cursor: pointer;
            }}
            .controls button:hover {{
                background: #2980b9;
            }}
            .topics {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                gap: 20px;
            }}
            .topic-card {{
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 20px;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .topic-title {{
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                font-size: 1.1em;
            }}
            .topic-source {{
                color: #7f8c8d;
                font-size: 0.9em;
                margin-bottom: 10px;
            }}
            .topic-content {{
                color: #34495e;
                line-height: 1.5;
                margin-bottom: 10px;
            }}
            .topic-meta {{
                display: flex;
                justify-content: space-between;
                font-size: 0.8em;
                color: #95a5a6;
            }}
            .loading {{
                text-align: center;
                padding: 40px;
                color: #7f8c8d;
            }}
            .error {{
                color: #e74c3c;
                text-align: center;
                padding: 20px;
                background: #fdf2f2;
                border-radius: 4px;
                margin-bottom: 20px;
            }}
            .admin-section {{
                background: #ecf0f1;
                padding: 20px;
                border-radius: 6px;
                margin-bottom: 30px;
            }}
            .admin-section h2 {{
                color: #2c3e50;
                margin-top: 0;
            }}
            .admin-buttons {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .admin-button {{
                background: #e74c3c;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .admin-button.success {{
                background: #27ae60;
            }}
            .admin-button:hover {{
                opacity: 0.9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Jeen.ai Documentation Dashboard</h1>
            
            <div class="admin-section">
                <h2>Database Management</h2>
                <div class="admin-buttons">
                    <button class="admin-button" onclick="testConnectivity()">Test Connectivity</button>
                    <button class="admin-button" onclick="checkDatabaseStatus()">Check Database Status</button>
                    <button class="admin-button" onclick="fixDatabaseSchema()">Fix Database Schema</button>
                    <button class="admin-button success" onclick="processAllDocuments()">Process All Documents</button>
                    <button class="admin-button" onclick="clearDatabase()">Clear Database</button>
                </div>
                <div id="admin-output" style="margin-top: 15px; padding: 10px; background: white; border-radius: 4px; min-height: 40px;"></div>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <h3 id="total-topics">-</h3>
                    <p>Total Documents</p>
                </div>
                <div class="stat-card">
                    <h3 id="avg-length">-</h3>
                    <p>Avg Length</p>
                </div>
                <div class="stat-card">
                    <h3 id="ready-status">-</h3>
                    <p>Bot Ready</p>
                </div>
            </div>
            
            <div class="controls">
                <input type="text" id="search-input" placeholder="Search topics..." />
                <select id="source-filter">
                    <option value="">All Sources</option>
                </select>
                <button onclick="loadTopics()">🔄 Refresh</button>
                <button onclick="searchTopics()">🔍 Search</button>
            </div>
            
            <div id="error-message" class="error" style="display: none;"></div>
            <div id="topics-container" class="topics"></div>
            <div id="loading" class="loading">Loading topics...</div>
        </div>

        <script>
            const baseUrl = '{base_url}';
            let currentTopics = [];
            
            // Debug: show the base URL
            console.log('Base URL:', baseUrl);

            async function apiCall(endpoint, options = {{}}) {{
                // Use relative URLs instead of base_url to avoid cross-origin issues
                const url = endpoint.startsWith('/') ? endpoint : `/${{endpoint}}`;
                console.log('Making API call to:', url);
                
                try {{
                    const response = await fetch(url, {{
                        headers: {{
                            'Content-Type': 'application/json',
                            ...options.headers
                        }},
                        ...options
                    }});
                    
                    if (!response.ok) {{
                        throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                    }}
                    
                    return await response.json();
                }} catch (error) {{
                    console.error('API Error:', error);
                    console.error('Failed URL:', url);
                    throw error;
                }}
            }}

            async function loadStats() {{
                try {{
                    const stats = await apiCall('/dashboard/stats');
                    document.getElementById('total-topics').textContent = stats.total_topics;
                    document.getElementById('avg-length').textContent = Math.round(stats.average_content_length);
                    document.getElementById('ready-status').textContent = stats.ready_for_queries ? '✅' : '❌';
                }} catch (error) {{
                    console.error('Failed to load stats:', error);
                }}
            }}

            async function loadTopics() {{
                const loading = document.getElementById('loading');
                const container = document.getElementById('topics-container');
                const errorDiv = document.getElementById('error-message');
                
                loading.style.display = 'block';
                container.innerHTML = '';
                errorDiv.style.display = 'none';

                try {{
                    const sourceFilter = document.getElementById('source-filter').value;
                    const params = sourceFilter ? `?source=${{encodeURIComponent(sourceFilter)}}` : '';
                    const data = await apiCall(`/dashboard/topics${{params}}`);
                    
                    currentTopics = data.topics;
                    
                    // Update source filter options
                    updateSourceFilter(data.filters.available_sources);
                    
                    // Render topics
                    renderTopics(currentTopics);
                    
                }} catch (error) {{
                    showError(`Failed to load topics: ${{error.message}}`);
                }} finally {{
                    loading.style.display = 'none';
                }}
            }}

            function updateSourceFilter(sources) {{
                const select = document.getElementById('source-filter');
                const currentValue = select.value;
                
                // Keep existing options, add new ones
                const existingOptions = Array.from(select.options).map(opt => opt.value);
                
                sources.forEach(source => {{
                    if (!existingOptions.includes(source)) {{
                        const option = document.createElement('option');
                        option.value = source;
                        option.textContent = source;
                        select.appendChild(option);
                    }}
                }});
                
                select.value = currentValue;
            }}

            function renderTopics(topics) {{
                const container = document.getElementById('topics-container');
                
                if (topics.length === 0) {{
                    container.innerHTML = '<div class="loading">No topics found. Use "Process All Documents" to load documentation.</div>';
                    return;
                }}
                
                container.innerHTML = topics.map(topic => `
                    <div class="topic-card">
                        <div class="topic-title">${{escapeHtml(topic.subject)}}</div>
                        <div class="topic-source">📁 ${{escapeHtml(topic.source)}}</div>
                        <div class="topic-content">${{escapeHtml(topic.content)}}</div>
                        <div class="topic-meta">
                            <span>📝 ${{topic.content_length}} chars</span>
                            <span>📅 ${{new Date(topic.start_time).toLocaleDateString()}}</span>
                        </div>
                    </div>
                `).join('');
            }}

            async function searchTopics() {{
                const query = document.getElementById('search-input').value.trim();
                
                if (!query) {{
                    renderTopics(currentTopics);
                    return;
                }}
                
                try {{
                    const data = await apiCall(`/dashboard/search?q=${{encodeURIComponent(query)}}`);
                    renderTopics(data.results);
                }} catch (error) {{
                    showError(`Search failed: ${{error.message}}`);
                }}
            }}

            // Admin functions
            async function testConnectivity() {{
                const output = document.getElementById('admin-output');
                output.innerHTML = 'Testing connectivity...';
                
                try {{
                    // Test main app endpoint first
                    const result = await apiCall('/debug-test');
                    output.innerHTML = `<span style="color: green;">✅ Main app: ${{result.message}}</span>`;
                    
                    // Then test admin endpoint
                    try {{
                        const adminResult = await apiCall('/admin/test');
                        output.innerHTML += `<br><span style="color: green;">✅ Admin: ${{adminResult.message}}</span>`;
                    }} catch (adminError) {{
                        output.innerHTML += `<br><span style="color: red;">❌ Admin Error: ${{adminError.message}}</span>`;
                    }}
                }} catch (error) {{
                    output.innerHTML = `<span style="color: red;">❌ Main App Error: ${{error.message}}</span>`;
                }}
            }}

            async function checkDatabaseStatus() {{
                const output = document.getElementById('admin-output');
                output.innerHTML = 'Checking database status...';
                
                try {{
                    const result = await apiCall('/admin/database/status');
                    output.innerHTML = `
                        <strong>Database Status:</strong><br>
                        Tables: ${{result.tables.join(', ')}}<br>
                        Table counts: ${{JSON.stringify(result.table_counts, null, 2)}}
                    `;
                }} catch (error) {{
                    output.innerHTML = `<span style="color: red;">Error: ${{error.message}}</span>`;
                }}
            }}

            async function fixDatabaseSchema() {{
                const output = document.getElementById('admin-output');
                output.innerHTML = 'Fixing database schema...';
                
                try {{
                    const result = await apiCall('/admin/database/fix-schema', {{ method: 'POST' }});
                    output.innerHTML = `<span style="color: green;">✅ ${{result.message}}</span>`;
                    setTimeout(loadStats, 1000);
                }} catch (error) {{
                    output.innerHTML = `<span style="color: red;">❌ Error: ${{error.message}}</span>`;
                }}
            }}

            async function processAllDocuments() {{
                const output = document.getElementById('admin-output');
                output.innerHTML = 'Processing all documents from /documentation folder...';
                
                try {{
                    const result = await apiCall('/process_all_documentation', {{ method: 'POST' }});
                    output.innerHTML = `<span style="color: green;">✅ ${{result.message}}</span>`;
                    setTimeout(() => {{
                        loadStats();
                        loadTopics();
                    }}, 1000);
                }} catch (error) {{
                    output.innerHTML = `<span style="color: red;">❌ Error: ${{error.message}}</span>`;
                }}
            }}

            async function clearDatabase() {{
                if (!confirm('Are you sure you want to clear all database data?')) return;
                
                const output = document.getElementById('admin-output');
                output.innerHTML = 'Clearing database...';
                
                try {{
                    const result = await apiCall('/admin/database/clear-data', {{ method: 'POST' }});
                    output.innerHTML = `<span style="color: green;">✅ ${{result.message}}</span>`;
                    setTimeout(() => {{
                        loadStats();
                        loadTopics();
                    }}, 1000);
                }} catch (error) {{
                    output.innerHTML = `<span style="color: red;">❌ Error: ${{error.message}}</span>`;
                }}
            }}

            function showError(message) {{
                const errorDiv = document.getElementById('error-message');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
            }}

            function escapeHtml(text) {{
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }}

            // Initialize
            document.getElementById('search-input').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    searchTopics();
                }}
            }});

            // Load initial data
            loadStats();
            loadTopics();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)