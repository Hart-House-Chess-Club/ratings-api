import requests
import datetime
import os
import pymongo
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import ORJSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

from src.scraper import fide_scraper
from src.scraper.ratinglists import db as ratings_db
from src.scraper.ratinglists.updater import update_all_rating_lists, update_cfc_rating_list, update_fide_rating_list

# Load environment variables
load_dotenv()

# Helper function to get GA tracking ID
def get_ga_tracking_id():
    return os.getenv("GA_TRACKING_ID", "G-JSFHZ4X5YL")

# Google Analytics Middleware
class GoogleAnalyticsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ga_tracking_id: str = None):
        super().__init__(app)
        self.ga_tracking_id = ga_tracking_id or os.getenv("GA_TRACKING_ID", "G-JSFHZ4X5YL")
        
    async def dispatch(self, request: Request, call_next):
        # Track the request start time
        start_time = datetime.datetime.now()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (datetime.datetime.now() - start_time).total_seconds()
        
        # Log API usage (you can extend this to send to GA4 via Measurement Protocol)
        if not request.url.path.startswith("/static") and not request.url.path.startswith("/favicon"):
            print(f"API Request: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        
        return response

app = FastAPI(
    title=os.getenv("API_TITLE", "Chess Ratings API"),
    version=os.getenv("API_VERSION", "2.0.0"),
    description=os.getenv("API_DESCRIPTION", "Highly reliable, free, chess ratings API for FIDE, CFC, and other rating systems."),
    default_response_class=ORJSONResponse,
    docs_url=None,  # Disable default docs to use custom template
    redoc_url=None
)

# Add Google Analytics middleware
app.add_middleware(GoogleAnalyticsMiddleware)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Custom docs endpoint with Google Analytics
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    ga_id = get_ga_tracking_id()
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <!-- Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{ga_id}');
        </script>
        
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chess Ratings API - ChessTools</title>
        <link type="text/css" rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.25.3/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            border: "hsl(220 13% 91%)",
                            input: "hsl(220 13% 91%)",
                            ring: "hsl(224 71.4% 4.1%)",
                            background: "hsl(0 0% 100%)",
                            foreground: "hsl(224 71.4% 4.1%)",
                            primary: {{
                                DEFAULT: "hsl(220.9 39.3% 11%)",
                                foreground: "hsl(210 20% 98%)",
                            }},
                            secondary: {{
                                DEFAULT: "hsl(220 14.3% 90%)",
                                foreground: "hsl(220.9 39.3% 8%)",
                            }},
                            destructive: {{
                                DEFAULT: "hsl(0 84.2% 60.2%)",
                                foreground: "hsl(210 20% 98%)",
                            }},
                            muted: {{
                                DEFAULT: "hsl(220 14.3% 95.9%)",
                                foreground: "hsl(220 8.9% 46.1%)",
                            }},
                            accent: {{
                                DEFAULT: "hsl(220 14.3% 95.9%)",
                                foreground: "hsl(220.9 39.3% 11%)",
                            }},
                            popover: {{
                                DEFAULT: "hsl(0 0% 100%)",
                                foreground: "hsl(224 71.4% 4.1%)",
                            }},
                            card: {{
                                DEFAULT: "hsl(0 0% 100%)",
                                foreground: "hsl(224 71.4% 4.1%)",
                            }}
                        }},
                        borderRadius: {{
                            lg: "0.75rem",
                            md: "calc(0.75rem - 2px)",
                            sm: "calc(0.5rem - 4px)",
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; }}
        </style>
    </head>
    <body class="bg-background text-foreground">
        <!-- Navigation -->
        <nav class="bg-primary p-4 sticky top-0 z-50">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/" class="flex items-center gap-2">
                    <svg class="h-8 w-8 text-primary-foreground" fill="currentColor" viewBox="0 0 375 374.999991" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <clipPath id="2e198c8fd0">
                                <path d="M 104 250.613281 L 271 250.613281 L 271 356 L 104 356 Z M 104 250.613281 " clip-rule="nonzero"/>
                            </clipPath>
                            <clipPath id="352a3390ed">
                                <path d="M 104 19 L 267.605469 19 L 267.605469 188.285156 L 104 188.285156 Z M 104 19 " clip-rule="nonzero"/>
                            </clipPath>
                        </defs>
                        <g clip-path="url(#2e198c8fd0)">
                            <path fill="#ffbe2d" d="M 151.894531 272.488281 L 158.953125 186.238281 L 216.015625 186.238281 L 223.074219 272.488281 Z M 230.359375 272.488281 L 143.855469 272.488281 C 143.855469 286.394531 136.605469 299.636719 126.878906 308.867188 L 115.957031 319.226562 C 112.636719 321.332031 110.597656 325.152344 110.597656 329.289062 C 110.597656 335.75 115.496094 340.988281 121.539062 340.980469 L 253.4375 340.921875 C 259.480469 340.921875 264.371094 335.683594 264.371094 329.230469 L 264.371094 329.222656 C 264.371094 325.089844 262.332031 321.265625 259.007812 319.160156 L 245.949219 307.015625 C 236.644531 298.363281 231.867188 286.042969 231.214844 272.875 Z M 270.265625 348.164062 C 270.265625 344.191406 267.050781 340.980469 263.082031 340.980469 L 111.886719 340.980469 C 107.917969 340.980469 104.703125 344.191406 104.703125 348.164062 C 104.703125 352.132812 107.917969 355.347656 111.886719 355.347656 L 263.082031 355.347656 C 267.050781 355.347656 270.265625 352.132812 270.265625 348.164062 Z M 239.277344 177.484375 C 239.277344 172.625 235.34375 168.6875 230.484375 168.6875 L 144.484375 168.6875 C 139.625 168.6875 135.691406 172.625 135.691406 177.484375 C 135.691406 182.34375 139.625 186.277344 144.484375 186.277344 L 230.484375 186.277344 C 235.34375 186.277344 239.277344 182.34375 239.277344 177.484375 Z M 233.511719 159.894531 C 233.511719 155.035156 229.578125 151.097656 224.71875 151.097656 L 150.25 151.097656 C 145.390625 151.097656 141.457031 155.035156 141.457031 159.894531 C 141.457031 164.753906 145.390625 168.6875 150.25 168.6875 L 224.710938 168.6875 C 229.578125 168.6875 233.511719 164.753906 233.511719 159.894531 Z M 211.625 64.058594 C 211.625 59.199219 207.6875 55.261719 202.828125 55.261719 L 172.136719 55.261719 C 167.277344 55.261719 163.34375 59.199219 163.34375 64.058594 C 163.34375 68.917969 167.277344 72.855469 172.136719 72.855469 L 202.820312 72.855469 C 207.6875 72.855469 211.625 68.917969 211.625 64.058594 Z M 229.570312 72.855469 L 145.398438 72.855469 C 138.921875 72.855469 134.195312 79.003906 135.882812 85.265625 L 153.558594 151.097656 L 221.417969 151.097656 L 239.09375 85.265625 C 240.773438 79.003906 236.054688 72.855469 229.570312 72.855469 Z M 206.539062 31 L 195.183594 31 L 195.183594 19.644531 L 182.277344 19.644531 L 182.277344 31 L 170.921875 31 L 170.921875 43.917969 L 182.277344 43.917969 L 182.277344 55.269531 L 195.191406 55.269531 L 195.191406 43.90625 L 206.546875 43.90625 L 206.546875 31 Z M 206.539062 31 " fill-opacity="1" fill-rule="nonzero"/>
                        </g>
                        <g clip-path="url(#352a3390ed)">
                            <path fill="#ffbe2d" d="M 151.894531 272.488281 L 158.953125 186.238281 L 216.015625 186.238281 L 223.074219 272.488281 Z M 230.359375 272.488281 L 143.855469 272.488281 C 143.855469 286.394531 136.605469 299.636719 126.878906 308.867188 L 115.957031 319.226562 C 112.636719 321.332031 110.597656 325.152344 110.597656 329.289062 C 110.597656 335.75 115.496094 340.988281 121.539062 340.980469 L 253.4375 340.921875 C 259.480469 340.921875 264.371094 335.683594 264.371094 329.230469 L 264.371094 329.222656 C 264.371094 325.089844 262.332031 321.265625 259.007812 319.160156 L 245.949219 307.015625 C 236.644531 298.363281 231.867188 286.042969 231.214844 272.875 Z M 270.265625 348.164062 C 270.265625 344.191406 267.050781 340.980469 263.082031 340.980469 L 111.886719 340.980469 C 107.917969 340.980469 104.703125 344.191406 104.703125 348.164062 C 104.703125 352.132812 107.917969 355.347656 111.886719 355.347656 L 263.082031 355.347656 C 267.050781 355.347656 270.265625 352.132812 270.265625 348.164062 Z M 239.277344 177.484375 C 239.277344 172.625 235.34375 168.6875 230.484375 168.6875 L 144.484375 168.6875 C 139.625 168.6875 135.691406 172.625 135.691406 177.484375 C 135.691406 182.34375 139.625 186.277344 144.484375 186.277344 L 230.484375 186.277344 C 235.34375 186.277344 239.277344 182.34375 239.277344 177.484375 Z M 233.511719 159.894531 C 233.511719 155.035156 229.578125 151.097656 224.71875 151.097656 L 150.25 151.097656 C 145.390625 151.097656 141.457031 155.035156 141.457031 159.894531 C 141.457031 164.753906 145.390625 168.6875 150.25 168.6875 L 224.710938 168.6875 C 229.578125 168.6875 233.511719 164.753906 233.511719 159.894531 Z M 211.625 64.058594 C 211.625 59.199219 207.6875 55.261719 202.828125 55.261719 L 172.136719 55.261719 C 167.277344 55.261719 163.34375 59.199219 163.34375 64.058594 C 163.34375 68.917969 167.277344 72.855469 172.136719 72.855469 L 202.820312 72.855469 C 207.6875 72.855469 211.625 68.917969 211.625 64.058594 Z M 229.570312 72.855469 L 145.398438 72.855469 C 138.921875 72.855469 134.195312 79.003906 135.882812 85.265625 L 153.558594 151.097656 L 221.417969 151.097656 L 239.09375 85.265625 C 240.773438 79.003906 236.054688 72.855469 229.570312 72.855469 Z M 206.539062 31 L 195.183594 31 L 195.183594 19.644531 L 182.277344 19.644531 L 182.277344 31 L 170.921875 31 L 170.921875 43.917969 L 182.277344 43.917969 L 182.277344 55.269531 L 195.191406 55.269531 L 195.191406 43.90625 L 206.546875 43.90625 L 206.546875 31 Z M 206.539062 31 " fill-opacity="1" fill-rule="nonzero"/>
                        </g>
                    </svg>
                    <span class="text-xl font-bold text-primary-foreground">ChessTools</span>
                </a>

                <!-- Desktop Navigation -->
                <div class="hidden md:flex items-center gap-6">
                    <div class="relative group">
                        <button class="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground px-4 py-2 rounded-md transition-colors">
                            Tools
                        </button>
                        <div class="absolute right-0 mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                            <div class="py-1">
                                <a href="https://chesstools.org/generator" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">FEN to PNG</a>
                                <a href="https://chesstools.org/board" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">Board</a>
                                <a href="https://chesstools.org/analysis" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">Analysis</a>
                                <a href="https://gif.chesstools.org/" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">GIF Generator</a>
                                <a href="/" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground font-medium">Ratings API</a>
                                <a href="https://chesstools.org/estimator" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">Ratings Estimator</a>
                                <a href="https://cfc.chesstools.org/" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">CFC Ratings Processor</a>
                            </div>
                        </div>
                    </div>
                    <a href="https://chesstools.org/play" class="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground px-4 py-2 rounded-md transition-colors">Play</a>
                    <a href="https://chesstools.org/about" class="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground px-4 py-2 rounded-md transition-colors">About</a>
                </div>

                <!-- Mobile Navigation -->
                <div class="md:hidden">
                    <button id="mobile-menu-btn" class="bg-primary-foreground text-primary p-2 rounded-md">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Mobile Menu -->
            <div id="mobile-menu" class="hidden md:hidden mt-4 bg-primary border-t border-primary-foreground/20">
                <div class="flex flex-col gap-2 py-4">
                    <a href="https://chesstools.org/board" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Board</a>
                    <a href="https://chesstools.org/play" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Play</a>
                    <a href="https://chesstools.org/analysis" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Analysis</a>
                    <a href="https://chesstools.org/estimator" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Ratings Estimator</a>
                    <a href="https://chesstools.org/generator" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Board Generator</a>
                    <a href="https://gif.chesstools.org/" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Chess GIF Generator</a>
                    <a href="/" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors font-medium">Ratings API</a>
                    <a href="https://chesstools.org/about" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">About</a>
                    <a href="https://cfc.chesstools.org/" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">CFC Ratings Processor</a>
                </div>
            </div>
        </nav>

        <!-- API Documentation Content -->
        <div class="container mx-auto px-4 py-8">
            <div class="bg-card rounded-lg shadow-sm border border-border p-6 mb-6">
                <h1 class="text-3xl font-bold text-foreground mb-2">Chess Ratings API Documentation</h1>
                <p class="text-muted-foreground">Highly reliable, free, chess ratings API for FIDE, CFC, and other rating systems.</p>
            </div>
            
            <div id="swagger-ui" class="bg-card rounded-lg shadow-sm border border-border"></div>
        </div>
        
        <script src="https://unpkg.com/swagger-ui-dist@5.25.3/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.25.3/swagger-ui-standalone-preset.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "StandaloneLayout",
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true
        }})
        
        // Mobile menu toggle
        document.getElementById('mobile-menu-btn').addEventListener('click', function() {{
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('hidden');
        }});
        
        // Track page view
        gtag('event', 'page_view', {{
            page_title: 'Chess Ratings API - Documentation',
            page_location: window.location.href
        }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Custom docs HTML with Google Analytics embedded
@app.get("/", include_in_schema=False)
def home():
    ga_id = get_ga_tracking_id()
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <!-- Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{ga_id}');
        </script>
        
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chess Ratings API - ChessTools</title>
        <meta name="description" content="Highly reliable, free, chess ratings API for FIDE, CFC, and other rating systems.">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            border: "hsl(220 13% 91%)",
                            input: "hsl(220 13% 91%)",
                            ring: "hsl(224 71.4% 4.1%)",
                            background: "hsl(0 0% 100%)",
                            foreground: "hsl(224 71.4% 4.1%)",
                            primary: {{
                                DEFAULT: "hsl(220.9 39.3% 11%)",
                                foreground: "hsl(210 20% 98%)",
                            }},
                            secondary: {{
                                DEFAULT: "hsl(220 14.3% 90%)",
                                foreground: "hsl(220.9 39.3% 8%)",
                            }},
                            destructive: {{
                                DEFAULT: "hsl(0 84.2% 60.2%)",
                                foreground: "hsl(210 20% 98%)",
                            }},
                            muted: {{
                                DEFAULT: "hsl(220 14.3% 95.9%)",
                                foreground: "hsl(220 8.9% 46.1%)",
                            }},
                            accent: {{
                                DEFAULT: "hsl(220 14.3% 95.9%)",
                                foreground: "hsl(220.9 39.3% 11%)",
                            }},
                            popover: {{
                                DEFAULT: "hsl(0 0% 100%)",
                                foreground: "hsl(224 71.4% 4.1%)",
                            }},
                            card: {{
                                DEFAULT: "hsl(0 0% 100%)",
                                foreground: "hsl(224 71.4% 4.1%)",
                            }}
                        }},
                        borderRadius: {{
                            lg: "0.75rem",
                            md: "calc(0.75rem - 2px)",
                            sm: "calc(0.5rem - 4px)",
                        }}
                    }}
                }}
            }}
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; }}
        </style>
    </head>
    <body class="bg-background text-foreground">
        <!-- Navigation -->
        <nav class="bg-primary p-4 sticky top-0 z-50">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/" class="flex items-center gap-2">
                    <svg class="h-8 w-8 text-primary-foreground" fill="currentColor" viewBox="0 0 375 374.999991" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <clipPath id="2e198c8fd0">
                                <path d="M 104 250.613281 L 271 250.613281 L 271 356 L 104 356 Z M 104 250.613281 " clip-rule="nonzero"/>
                            </clipPath>
                            <clipPath id="352a3390ed">
                                <path d="M 104 19 L 267.605469 19 L 267.605469 188.285156 L 104 188.285156 Z M 104 19 " clip-rule="nonzero"/>
                            </clipPath>
                        </defs>
                        <g clip-path="url(#2e198c8fd0)">
                            <path fill="#ffbe2d" d="M 151.894531 272.488281 L 158.953125 186.238281 L 216.015625 186.238281 L 223.074219 272.488281 Z M 230.359375 272.488281 L 143.855469 272.488281 C 143.855469 286.394531 136.605469 299.636719 126.878906 308.867188 L 115.957031 319.226562 C 112.636719 321.332031 110.597656 325.152344 110.597656 329.289062 C 110.597656 335.75 115.496094 340.988281 121.539062 340.980469 L 253.4375 340.921875 C 259.480469 340.921875 264.371094 335.683594 264.371094 329.230469 L 264.371094 329.222656 C 264.371094 325.089844 262.332031 321.265625 259.007812 319.160156 L 245.949219 307.015625 C 236.644531 298.363281 231.867188 286.042969 231.214844 272.875 Z M 270.265625 348.164062 C 270.265625 344.191406 267.050781 340.980469 263.082031 340.980469 L 111.886719 340.980469 C 107.917969 340.980469 104.703125 344.191406 104.703125 348.164062 C 104.703125 352.132812 107.917969 355.347656 111.886719 355.347656 L 263.082031 355.347656 C 267.050781 355.347656 270.265625 352.132812 270.265625 348.164062 Z M 239.277344 177.484375 C 239.277344 172.625 235.34375 168.6875 230.484375 168.6875 L 144.484375 168.6875 C 139.625 168.6875 135.691406 172.625 135.691406 177.484375 C 135.691406 182.34375 139.625 186.277344 144.484375 186.277344 L 230.484375 186.277344 C 235.34375 186.277344 239.277344 182.34375 239.277344 177.484375 Z M 233.511719 159.894531 C 233.511719 155.035156 229.578125 151.097656 224.71875 151.097656 L 150.25 151.097656 C 145.390625 151.097656 141.457031 155.035156 141.457031 159.894531 C 141.457031 164.753906 145.390625 168.6875 150.25 168.6875 L 224.710938 168.6875 C 229.578125 168.6875 233.511719 164.753906 233.511719 159.894531 Z M 211.625 64.058594 C 211.625 59.199219 207.6875 55.261719 202.828125 55.261719 L 172.136719 55.261719 C 167.277344 55.261719 163.34375 59.199219 163.34375 64.058594 C 163.34375 68.917969 167.277344 72.855469 172.136719 72.855469 L 202.820312 72.855469 C 207.6875 72.855469 211.625 68.917969 211.625 64.058594 Z M 229.570312 72.855469 L 145.398438 72.855469 C 138.921875 72.855469 134.195312 79.003906 135.882812 85.265625 L 153.558594 151.097656 L 221.417969 151.097656 L 239.09375 85.265625 C 240.773438 79.003906 236.054688 72.855469 229.570312 72.855469 Z M 206.539062 31 L 195.183594 31 L 195.183594 19.644531 L 182.277344 19.644531 L 182.277344 31 L 170.921875 31 L 170.921875 43.917969 L 182.277344 43.917969 L 182.277344 55.269531 L 195.191406 55.269531 L 195.191406 43.90625 L 206.546875 43.90625 L 206.546875 31 Z M 206.539062 31 " fill-opacity="1" fill-rule="nonzero"/>
                        </g>
                        <g clip-path="url(#352a3390ed)">
                            <path fill="#ffbe2d" d="M 151.894531 272.488281 L 158.953125 186.238281 L 216.015625 186.238281 L 223.074219 272.488281 Z M 230.359375 272.488281 L 143.855469 272.488281 C 143.855469 286.394531 136.605469 299.636719 126.878906 308.867188 L 115.957031 319.226562 C 112.636719 321.332031 110.597656 325.152344 110.597656 329.289062 C 110.597656 335.75 115.496094 340.988281 121.539062 340.980469 L 253.4375 340.921875 C 259.480469 340.921875 264.371094 335.683594 264.371094 329.230469 L 264.371094 329.222656 C 264.371094 325.089844 262.332031 321.265625 259.007812 319.160156 L 245.949219 307.015625 C 236.644531 298.363281 231.867188 286.042969 231.214844 272.875 Z M 270.265625 348.164062 C 270.265625 344.191406 267.050781 340.980469 263.082031 340.980469 L 111.886719 340.980469 C 107.917969 340.980469 104.703125 344.191406 104.703125 348.164062 C 104.703125 352.132812 107.917969 355.347656 111.886719 355.347656 L 263.082031 355.347656 C 267.050781 355.347656 270.265625 352.132812 270.265625 348.164062 Z M 239.277344 177.484375 C 239.277344 172.625 235.34375 168.6875 230.484375 168.6875 L 144.484375 168.6875 C 139.625 168.6875 135.691406 172.625 135.691406 177.484375 C 135.691406 182.34375 139.625 186.277344 144.484375 186.277344 L 230.484375 186.277344 C 235.34375 186.277344 239.277344 182.34375 239.277344 177.484375 Z M 233.511719 159.894531 C 233.511719 155.035156 229.578125 151.097656 224.71875 151.097656 L 150.25 151.097656 C 145.390625 151.097656 141.457031 155.035156 141.457031 159.894531 C 141.457031 164.753906 145.390625 168.6875 150.25 168.6875 L 224.710938 168.6875 C 229.578125 168.6875 233.511719 164.753906 233.511719 159.894531 Z M 211.625 64.058594 C 211.625 59.199219 207.6875 55.261719 202.828125 55.261719 L 172.136719 55.261719 C 167.277344 55.261719 163.34375 59.199219 163.34375 64.058594 C 163.34375 68.917969 167.277344 72.855469 172.136719 72.855469 L 202.820312 72.855469 C 207.6875 72.855469 211.625 68.917969 211.625 64.058594 Z M 229.570312 72.855469 L 145.398438 72.855469 C 138.921875 72.855469 134.195312 79.003906 135.882812 85.265625 L 153.558594 151.097656 L 221.417969 151.097656 L 239.09375 85.265625 C 240.773438 79.003906 236.054688 72.855469 229.570312 72.855469 Z M 206.539062 31 L 195.183594 31 L 195.183594 19.644531 L 182.277344 19.644531 L 182.277344 31 L 170.921875 31 L 170.921875 43.917969 L 182.277344 43.917969 L 182.277344 55.269531 L 195.191406 55.269531 L 195.191406 43.90625 L 206.546875 43.90625 L 206.546875 31 Z M 206.539062 31 " fill-opacity="1" fill-rule="nonzero"/>
                        </g>
                    </svg>
                    <span class="text-xl font-bold text-primary-foreground">ChessTools</span>
                </a>

                <!-- Desktop Navigation -->
                <div class="hidden md:flex items-center gap-6">
                    <div class="relative group">
                        <button class="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground px-4 py-2 rounded-md transition-colors">
                            Tools
                        </button>
                        <div class="absolute right-0 mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                            <div class="py-1">
                                <a href="https://chesstools.org/generator" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">FEN to PNG</a>
                                <a href="https://chesstools.org/board" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">Board</a>
                                <a href="https://chesstools.org/analysis" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">Analysis</a>
                                <a href="https://gif.chesstools.org/" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">GIF Generator</a>
                                <a href="/" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground font-medium">Ratings API</a>
                                <a href="https://chesstools.org/estimator" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">Ratings Estimator</a>
                                <a href="https://cfc.chesstools.org/" class="block px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground">CFC Ratings Processor</a>
                            </div>
                        </div>
                    </div>
                    <a href="https://chesstools.org/play" class="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground px-4 py-2 rounded-md transition-colors">Play</a>
                    <a href="https://chesstools.org/about" class="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground px-4 py-2 rounded-md transition-colors">About</a>
                </div>

                <!-- Mobile Navigation -->
                <div class="md:hidden">
                    <button id="mobile-menu-btn" class="bg-primary-foreground text-primary p-2 rounded-md">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Mobile Menu -->
            <div id="mobile-menu" class="hidden md:hidden mt-4 bg-primary border-t border-primary-foreground/20">
                <div class="flex flex-col gap-2 py-4">
                    <a href="https://chesstools.org/board" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Board</a>
                    <a href="https://chesstools.org/play" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Play</a>
                    <a href="https://chesstools.org/analysis" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Analysis</a>
                    <a href="https://chesstools.org/estimator" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Ratings Estimator</a>
                    <a href="https://chesstools.org/generator" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Board Generator</a>
                    <a href="https://gif.chesstools.org/" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">Chess GIF Generator</a>
                    <a href="/" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors font-medium">Ratings API</a>
                    <a href="https://chesstools.org/about" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">About</a>
                    <a href="https://cfc.chesstools.org/" class="text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors">CFC Ratings Processor</a>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <section class="relative overflow-hidden bg-gradient-to-b from-primary/10 to-background py-20">
            <div class="container mx-auto px-4 relative z-10">
                <div class="text-center max-w-4xl mx-auto">
                    <h1 class="text-4xl md:text-6xl font-bold text-foreground mb-6">
                        Chess Ratings API
                    </h1>
                    <p class="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                        Highly reliable, free, chess ratings API for FIDE, CFC, and other rating systems. 
                        Access comprehensive chess player ratings data through our RESTful API.
                    </p>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="/docs" class="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2">
                            📚 API Documentation
                        </a>
                        <a href="/health" class="bg-secondary text-secondary-foreground hover:bg-secondary/90 px-8 py-3 rounded-lg font-semibold transition-colors inline-flex items-center gap-2">
                            🔍 Health Check
                        </a>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section class="py-20 bg-background">
            <div class="container mx-auto px-4">
                <div class="text-center mb-12">
                    <h2 class="text-3xl font-bold text-foreground mb-4">API Features</h2>
                    <p class="text-muted-foreground max-w-2xl mx-auto">
                        Access comprehensive chess ratings data with our reliable and fast API
                    </p>
                </div>
                
                <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                    <div class="bg-card border border-border rounded-lg p-6">
                        <div class="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                            <span class="text-2xl">🏆</span>
                        </div>
                        <h3 class="text-xl font-semibold text-foreground mb-3">FIDE Ratings</h3>
                        <p class="text-muted-foreground">Get top active players, detailed player information, and rating history from FIDE's official data.</p>
                    </div>
                    
                    <div class="bg-card border border-border rounded-lg p-6">
                        <div class="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                            <span class="text-2xl">🇨🇦</span>
                        </div>
                        <h3 class="text-xl font-semibold text-foreground mb-3">CFC Ratings</h3>
                        <p class="text-muted-foreground">Access Canadian chess ratings data with search capabilities and comprehensive player information.</p>
                    </div>
                    
                    <div class="bg-card border border-border rounded-lg p-6">
                        <div class="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                            <span class="text-2xl">🇺🇸</span>
                        </div>
                        <h3 class="text-xl font-semibold text-foreground mb-3">USCF Ratings</h3>
                        <p class="text-muted-foreground">Query US Chess Federation ratings with fast lookups and detailed player statistics.</p>
                    </div>
                    
                    <div class="bg-card border border-border rounded-lg p-6">
                        <div class="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                            <span class="text-2xl">⚡</span>
                        </div>
                        <h3 class="text-xl font-semibold text-foreground mb-3">Fast & Reliable</h3>
                        <p class="text-muted-foreground">Redis caching and MongoDB integration ensure quick responses and high availability.</p>
                    </div>
                    
                    <div class="bg-card border border-border rounded-lg p-6">
                        <div class="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                            <span class="text-2xl">🔍</span>
                        </div>
                        <h3 class="text-xl font-semibold text-foreground mb-3">Search Players</h3>
                        <p class="text-muted-foreground">Find players by name across all rating systems with powerful search capabilities.</p>
                    </div>
                    
                    <div class="bg-card border border-border rounded-lg p-6">
                        <div class="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                            <span class="text-2xl">📊</span>
                        </div>
                        <h3 class="text-xl font-semibold text-foreground mb-3">Health Monitoring</h3>
                        <p class="text-muted-foreground">Real-time system status and health checks to ensure optimal API performance.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- CTA Section -->
        <section class="py-20 bg-primary/5">
            <div class="container mx-auto px-4 text-center">
                <h2 class="text-3xl font-bold text-foreground mb-4">Ready to Get Started?</h2>
                <p class="text-muted-foreground mb-8 max-w-2xl mx-auto">
                    Explore our comprehensive API documentation and start integrating chess ratings data into your applications today.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <a href="/docs" class="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-3 rounded-lg font-semibold transition-colors">
                        View API Documentation
                    </a>
                    <a href="https://chesstools.org" class="bg-secondary text-secondary-foreground hover:bg-secondary/90 px-8 py-3 rounded-lg font-semibold transition-colors">
                        Explore ChessTools
                    </a>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="bg-primary text-primary-foreground py-8">
            <div class="container mx-auto px-4 text-center">
                <p>&copy; 2025 ChessTools. Open source chess tools and APIs.</p>
            </div>
        </footer>
        
        <script>
            // Mobile menu toggle
            document.getElementById('mobile-menu-btn').addEventListener('click', function() {{
                const menu = document.getElementById('mobile-menu');
                menu.classList.toggle('hidden');
            }});
            
            // Track page view
            gtag('event', 'page_view', {{
                page_title: 'Chess Ratings API - ChessTools',
                page_location: window.location.href
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/fide/top_active/", tags=["FIDE"])
async def top_players(limit: int = 100, history: bool = False):
  response = fide_scraper.get_top_players(limit=limit, history=history)
  return response

# FIDE endpoints
@app.get("/fide/top_by_rating", tags=["FIDE"])
async def get_top_fide_players(limit: int = 100):
  """Get top rated FIDE players from the rating list database."""
  return ratings_db.get_top_rated_fide(limit)

@app.get("/fide/player_history/", tags=["FIDE"])
async def player_history(fide_id: str):
  response = fide_scraper.get_player_history(fide_id=fide_id)
  return response

@app.get("/fide/{player_id}", tags=["FIDE"])
async def get_fide_player_rating(player_id: str):
  """Get a FIDE player's rating data from the rating list database."""
  player = ratings_db.get_fide_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player


@app.get("/fide/player_info/", tags=["FIDE"])
async def player_info(fide_id: str, history: bool = False):
  response = fide_scraper.get_player_info(fide_id=fide_id, history=history)
  return response

@app.get("/cfc/top_by_rating", tags=["CFC"])
async def get_top_cfc_players(limit: int = 100):
  """Get top rated CFC players from the rating list database."""
  return ratings_db.get_top_rated_cfc(limit)

@app.get("/cfc/{player_id}", tags=["CFC"])
async def get_cfc_player_rating(player_id: str):
  """Get a CFC player's rating data from the rating list database."""
  player = ratings_db.get_cfc_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player

@app.get("/uscf/top_by_rating", tags=["USCF"])
async def get_top_uscf_players(limit: int = 100):
  """Get top rated USCF players from the rating list database."""
  return ratings_db.get_top_rated_uscf(limit)

@app.get("/uscf/{player_id}", tags=["USCF"])
async def get_uscf_player_rating(player_id: int):
  """Get a USCF player's rating data from the rating list database."""
  player = ratings_db.get_uscf_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player

@app.get("/ratinglist/search", tags=["All"])
async def search_players(query: str, list_type: str = "fide"):
  """Search for players by name in either FIDE or CFC rating lists."""
  if list_type.lower() not in ["fide", "cfc"]:
    raise HTTPException(status_code=400, detail="list_type must be 'fide' or 'cfc'")
  
  results = ratings_db.search_player(query, list_type)
  return results

@app.get("/ratinglist/metadata", tags=["All"])
async def get_rating_lists_metadata():
  """Get metadata about the rating lists (last update, etc.)"""
  return ratings_db.get_rating_list_metadata()

# @app.post("/update", tags=["System"])
# async def trigger_rating_lists_update(background_tasks: BackgroundTasks):
#   """Trigger an update of the rating lists (admin only)"""
#   # In a production environment, you would add authentication here
  
#   # Run update in the background to avoid blocking the request
#   background_tasks.add_task(update_all_rating_lists)
  
#   return {"status": "update_started", "message": "Rating list update has been started in the background"}

# @app.post("/ratinglist/reset", tags=["System"])
# async def reset_rating_lists_db(background_tasks: BackgroundTasks):
#     """Reset the rating lists database collections (admin only)"""
#     # In a production environment, you would add authentication here
    
#     from src.scraper.ratinglists.db import reset_collections
    
#     success = reset_collections()
#     if not success:
#         raise HTTPException(status_code=500, detail="Failed to reset rating lists database")
    
#     # Start a background task to reinitialize the database
#     background_tasks.add_task(update_all_rating_lists)
    
#     return {"status": "reset_completed", "message": "Rating lists database has been reset and reinitialization started"}

@app.get("/health", tags=["All"])
async def health_check():
    """Health check endpoint for monitoring the API status"""
    health_status = {
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Redis connection
    try:
        from src.scraper.cache import redis_client
        redis_info = redis_client.info()
        health_status["services"]["redis"] = {
            "status": "ok",
            "version": redis_info.get("redis_version", "unknown")
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check MongoDB connection
    try:
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        server_info = mongo_client.server_info()
        fide_count = ratings_db.fide_collection.count_documents({})
        cfc_count = ratings_db.cfc_collection.count_documents({})
        uscf_count = ratings_db.uscf_collection.count_documents({})
        
        health_status["services"]["mongodb"] = {
            "status": "ok",
            "version": server_info.get("version", "unknown"),
            "fide_players": fide_count,
            "cfc_players": cfc_count,
            "uscf_players": uscf_count
        }
    except Exception as e:
        health_status["services"]["mongodb"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Get rating list last refresh dates from metadata
    try:
        metadata = ratings_db.get_rating_list_metadata()
        if metadata:
            rating_lists_status = {}
            
            # FIDE last update
            if "fide_last_updated" in metadata:
                rating_lists_status["fide_last_refreshed"] = metadata["fide_last_updated"]
            
            # CFC last update  
            if "cfc_last_updated" in metadata:
                rating_lists_status["cfc_last_refreshed"] = metadata["cfc_last_updated"]
                
            # USCF last update
            if "uscf_last_updated" in metadata:
                rating_lists_status["uscf_last_refreshed"] = metadata["uscf_last_updated"]
            
            if rating_lists_status:
                health_status["rating_lists"] = rating_lists_status
                
    except Exception as e:
        health_status["rating_lists"] = {
            "status": "error",
            "error": f"Could not retrieve metadata: {str(e)}"
        }
    
    # Check FIDE website accessibility for the web scraper
    try:
        fide_response = requests.get("https://ratings.fide.com", timeout=5)
        health_status["services"]["fide_website"] = {
            "status": "ok" if fide_response.status_code == 200 else "error",
            "status_code": fide_response.status_code
        }
    except Exception as e:
        health_status["services"]["fide_website"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status
