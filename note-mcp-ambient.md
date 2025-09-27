Here's a minimal FastMCP server that logs conversation insights and maintains ambient context:

```
#!/usr/bin/env python3
"""
Ambient Insights MCP Server
A minimal FastMCP server that passively observes conversations and logs insights.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import re

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data storage path
DATA_DIR = Path("./mcp_data")
DATA_DIR.mkdir(exist_ok=True)

@dataclass
class ConversationInsight:
    timestamp: str
    insight_type: str
    content: str
    context: str
    confidence: float
    
@dataclass
class UserContext:
    interests: List[str]
    skills: List[str] 
    current_projects: List[str]
    goals: List[str]
    preferences: Dict[str, Any]
    last_updated: str

class InsightDetector:
    """Detects various types of insights from conversation text"""
    
    @staticmethod
    def detect_learning_moment(text: str) -> Optional[str]:
        """Detect when user is learning something new"""
        learning_patterns = [
            r"i (didn't know|had no idea|never realized)",
            r"(wow|oh|interesting).{0,20}(i|that)",
            r"(makes sense|i see|i understand)",
            r"(learned|discovered|found out)"
        ]
        
        for pattern in learning_patterns:
            if re.search(pattern, text.lower()):
                return f"Learning moment detected: {text[:100]}..."
        return None
    
    @staticmethod
    def detect_problem_solving(text: str) -> Optional[str]:
        """Detect problem-solving discussions"""
        problem_patterns = [
            r"(how do i|how can i|help me)",
            r"(stuck|confused|struggling)",
            r"(problem|issue|challenge|difficulty)",
            r"(solution|fix|resolve|solve)"
        ]
        
        for pattern in problem_patterns:
            if re.search(pattern, text.lower()):
                return f"Problem-solving discussion: {text[:100]}..."
        return None
    
    @staticmethod
    def extract_interests(text: str) -> List[str]:
        """Extract potential user interests from text"""
        # Simple keyword extraction - could be enhanced with NLP
        interest_keywords = []
        
        # Look for "I like/love/enjoy" patterns
        like_pattern = r"i (like|love|enjoy|am interested in) ([^.!?]+)"
        matches = re.findall(like_pattern, text.lower())
        for _, interest in matches:
            interest_keywords.append(interest.strip())
        
        # Look for technology mentions
        tech_keywords = [
            "python", "javascript", "docker", "kubernetes", "ai", "machine learning",
            "react", "vue", "angular", "nodejs", "rust", "go", "java", "c++",
            "blockchain", "crypto", "web3", "apis", "databases", "sql"
        ]
        
        for keyword in tech_keywords:
            if keyword in text.lower():
                interest_keywords.append(keyword)
        
        return list(set(interest_keywords))

class AmbientInsightsServer:
    def __init__(self):
        self.insights_file = DATA_DIR / "insights.jsonl"
        self.context_file = DATA_DIR / "user_context.json"
        self.detector = InsightDetector()
        
    def save_insight(self, insight: ConversationInsight):
        """Save an insight to persistent storage"""
        with open(self.insights_file, "a") as f:
            f.write(json.dumps(asdict(insight)) + "\n")
        logger.info(f"Saved insight: {insight.insight_type}")
    
    def load_user_context(self) -> UserContext:
        """Load existing user context or create new one"""
        if self.context_file.exists():
            with open(self.context_file, "r") as f:
                data = json.load(f)
                return UserContext(**data)
        else:
            return UserContext(
                interests=[],
                skills=[],
                current_projects=[],
                goals=[],
                preferences={},
                last_updated=datetime.now().isoformat()
            )
    
    def save_user_context(self, context: UserContext):
        """Save user context to persistent storage"""
        context.last_updated = datetime.now().isoformat()
        with open(self.context_file, "w") as f:
            json.dump(asdict(context), f, indent=2)
    
    def update_context_from_text(self, text: str):
        """Update user context based on conversation text"""
        context = self.load_user_context()
        
        # Extract and merge new interests
        new_interests = self.detector.extract_interests(text)
        for interest in new_interests:
            if interest not in context.interests:
                context.interests.append(interest)
        
        # Look for project mentions
        project_patterns = [
            r"(working on|building|creating|developing) ([^.!?]+)",
            r"my (project|app|website|tool) ([^.!?]+)"
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text.lower())
            for _, project in matches:
                project = project.strip()
                if project and project not in context.current_projects:
                    context.current_projects.append(project)
        
        self.save_user_context(context)
    
    def analyze_conversation_turn(self, user_message: str, assistant_response: str):
        """Analyze a conversation turn for insights"""
        timestamp = datetime.now().isoformat()
        
        # Update user context
        self.update_context_from_text(user_message)
        
        # Detect learning moments
        learning_insight = self.detector.detect_learning_moment(user_message)
        if learning_insight:
            insight = ConversationInsight(
                timestamp=timestamp,
                insight_type="learning_moment",
                content=learning_insight,
                context=user_message[:200],
                confidence=0.7
            )
            self.save_insight(insight)
        
        # Detect problem-solving
        problem_insight = self.detector.detect_problem_solving(user_message)
        if problem_insight:
            insight = ConversationInsight(
                timestamp=timestamp,
                insight_type="problem_solving",
                content=problem_insight,
                context=user_message[:200],
                confidence=0.8
            )
            self.save_insight(insight)
    
    def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent insights for context injection"""
        insights = []
        if self.insights_file.exists():
            with open(self.insights_file, "r") as f:
                for line in f:
                    insights.append(json.loads(line))
        
        # Return most recent insights
        return sorted(insights, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_user_context(self) -> Dict:
        """Get current user context"""
        context = self.load_user_context()
        return asdict(context)

# Initialize the server
mcp = FastMCP("Ambient Insights")
insights_server = AmbientInsightsServer()

@mcp.tool()
def log_conversation_turn(user_message: str, assistant_response: str) -> str:
    """
    Log a conversation turn for ambient analysis.
    This should be called by the AI assistant after each exchange.
    """
    try:
        insights_server.analyze_conversation_turn(user_message, assistant_response)
        return "Conversation turn logged successfully"
    except Exception as e:
        logger.error(f"Error logging conversation: {e}")
        return f"Error logging conversation: {str(e)}"

@mcp.tool()
def get_user_context() -> Dict[str, Any]:
    """
    Get the current user context including interests, projects, and preferences.
    This can be used to personalize responses.
    """
    try:
        return insights_server.get_user_context()
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_recent_insights(limit: int = 5) -> List[Dict]:
    """
    Get recent conversation insights that might be relevant to the current discussion.
    """
    try:
        return insights_server.get_recent_insights(limit)
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def add_user_interest(interest: str) -> str:
    """
    Manually add a user interest to the context.
    """
    try:
        context = insights_server.load_user_context()
        if interest not in context.interests:
            context.interests.append(interest)
            insights_server.save_user_context(context)
            return f"Added interest: {interest}"
        else:
            return f"Interest '{interest}' already exists"
    except Exception as e:
        logger.error(f"Error adding interest: {e}")
        return f"Error adding interest: {str(e)}"

@mcp.tool()
def set_user_goal(goal: str) -> str:
    """
    Add or update a user goal.
    """
    try:
        context = insights_server.load_user_context()
        if goal not in context.goals:
            context.goals.append(goal)
            insights_server.save_user_context(context)
            return f"Added goal: {goal}"
        else:
            return f"Goal '{goal}' already exists"
    except Exception as e:
        logger.error(f"Error setting goal: {e}")
        return f"Error setting goal: {str(e)}"

if __name__ == "__main__":
    # Run the server
    mcp.run()
```

This is a minimal but functional ambient MCP server that:

## Features
- **Passive observation**: Analyzes conversation turns for learning moments and problem-solving patterns
- **Context building**: Tracks user interests, projects, and goals over time
- **Insight logging**: Stores insights in JSONL format for easy analysis
- **Persistent storage**: Maintains user context across sessions

## Key Tools
1. `log_conversation_turn()` - Main ambient function called after each exchange
2. `get_user_context()` - Returns accumulated user profile
3. `get_recent_insights()` - Retrieves relevant past insights
4. `add_user_interest()` - Manual context updates
5. `set_user_goal()` - Goal tracking

## Usage

**Requirements:**
```bash
pip install fastmcp
```

**Run the server:**
```bash
python ambient_mcp_server.py
```

**Docker deployment:**
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install fastmcp
EXPOSE 8000
CMD ["python", "ambient_mcp_server.py"]
```

## How it works
- The AI assistant calls `log_conversation_turn()` after each exchange
- The server analyzes text for patterns (learning, problems, interests)
- Context accumulates in `./mcp_data/user_context.json`
- Insights are logged to `./mcp_data/insights.jsonl`
- Future conversations can reference this accumulated context

The server starts simple but you can extend the `InsightDetector` class with more sophisticated NLP, add sentiment analysis, or integrate with external APIs for richer ambient intelligence.