# FILE: api_server.py
# PURPOSE: Runs the FastAPI web server to provide an API endpoint for browser plugins.

import re
import unicodedata

# --- Third-party web server libraries ---
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Import from our own modules ---
# We need the global list of results from the AI core
import ai_core

# We need the Colors class for printing messages
from config import Colors

# ===================================================================================
# --- API Data Models (Pydantic) ---
# ===================================================================================


class CandidateInfoResponse(BaseModel):
    name: str = Field(..., description="Candidate's name")
    score: float = Field(..., description="Final match score given by AI")
    best_position: str = Field(
        ..., description="The job position the AI thinks is the best match"
    )
    recommendation: str = Field(..., description="AI's final recommendation summary")
    market_competitiveness: str = Field(
        ..., description="AI's assessment of the candidate's market competitiveness"
    )


# ===================================================================================
# --- FastAPI Application Setup ---
# ===================================================================================

app = FastAPI(
    title="AI Recruiter Assistant API (v33.1 Enhanced)",
    description="Backend service providing candidate analysis data for browser plugins.",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests from any source (for the plugin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================================================================================
# --- Core API Logic ---
# ===================================================================================


def find_candidate_analysis(name_from_web: str):
    """Searches for a matching candidate in the in-memory list of session results."""
    if not name_from_web:
        return None

    normalized_web_name = re.sub(
        r"[\s\W_]+", "", unicodedata.normalize("NFKC", name_from_web)
    ).lower()
    if not normalized_web_name:
        return None

    # Search from the newest results backwards to get the latest analysis
    for result in reversed(ai_core.all_session_results):
        name_from_db = result.get("name")
        if name_from_db:
            normalized_db_name = re.sub(
                r"[\s\W_]+", "", unicodedata.normalize("NFKC", name_from_db)
            ).lower()

            # Fuzzy match: check if one name contains the other
            if (
                normalized_web_name in normalized_db_name
                or normalized_db_name in normalized_web_name
            ):
                score_text = result.get("score", "0")
                try:
                    score = float(re.sub(r"[^0-9.]", "", str(score_text)))
                except:
                    score = 0.0

                strengths = result.get("strengths", "N/A").strip()
                gaps = result.get("gaps", "N/A").strip()
                recommendation = (
                    f"【Core Strengths】:\n{strengths}\n\n【Potential Gaps】:\n{gaps}"
                )

                return {
                    "name": name_from_db,
                    "score": score,
                    "best_position": "N/A",  # This could be enhanced later
                    "recommendation": recommendation,
                    "market_competitiveness": "N/A",
                }
    return None


# ===================================================================================
# --- API Endpoints ---
# ===================================================================================


@app.get("/get_candidate_info", response_model=CandidateInfoResponse)
async def get_candidate_info(name: str):
    """
    This is the endpoint called by the Tampermonkey plugin.
    It receives a name and returns the AI analysis results for that candidate.
    """
    analysis_data = find_candidate_analysis(name)
    if analysis_data:
        return analysis_data
    else:
        # If not found, return a standard 404 Not Found error
        raise HTTPException(
            status_code=404,
            detail=f"Candidate data for '{name}' not found in the analyzed cache.",
        )


# ===================================================================================
# --- Server Runner Function ---
# ===================================================================================


def run_api_server():
    """Starts the FastAPI server in a separate thread."""
    print("\n" + "=" * 70)
    print(
        f"  [FastAPI Server] {Colors.BOLD}{Colors.GREEN}Started Successfully!{Colors.RESET}"
    )
    print(
        f"  - Plugin interface is listening on: {Colors.CYAN}http://127.0.0.1:5003/get_candidate_info{Colors.RESET}"
    )
    print(
        f"  - API documentation is available at: {Colors.CYAN}http://127.0.0.1:5003/docs{Colors.RESET}"
    )
    print("=" * 70)
    # Run the server using uvicorn on the specified port
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="warning")
