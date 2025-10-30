#!/usr/bin/env python3
"""
Simple Web Interface for Interview Chatbot with ChatGPT-style UI
"""

import os
import json
import openai
import uuid
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set environment variables manually")

# Initialize Flask app
app = Flask(__name__)

# Configuration
def load_config():
    """Load configuration from environment variables"""
    config = {
        'openai_api_key': os.getenv("OPENAI_API_KEY"),
        'port': int(os.environ.get('PORT', 5003)),
        'host': os.environ.get('HOST', '0.0.0.0'),
        'debug': os.environ.get('DEBUG', 'False').lower() == 'true'
    }
    # Railway and most cloud platforms set PORT dynamically
    # If PORT is provided, use it (Railway, Render, Heroku, etc.)
    
    # Validate required configuration
    if not config['openai_api_key']:
        error_msg = (
            "ERROR: OPENAI_API_KEY environment variable not set!\n\n"
            "To fix this, either:\n"
            "1. Set environment variable: export OPENAI_API_KEY='your-api-key-here'\n"
            "2. Create a .env file with: OPENAI_API_KEY=your-api-key-here\n"
            "3. Install python-dotenv: pip install python-dotenv"
        )
        print(error_msg)
        # In production, don't exit - let the app start and show error on first request
        # This allows Railway to show the service as running even if env var is missing
        if os.environ.get('PORT'):  # If PORT is set, we're in production
            print("Warning: App starting without API key. Add OPENAI_API_KEY to Railway variables.")
        else:
            exit(1)
    
    return config

# Load configuration
config = load_config()
OPENAI_API_KEY = config.get('openai_api_key')  # Use .get() to handle None gracefully

def generate_unique_id():
    """Generate a unique identifier for respondents"""
    # Create a timestamp-based identifier with some randomness
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8]
    
    # Combine timestamp and random part for uniqueness
    unique_id = f"{timestamp}-{random_part}"
    
    # Create a shorter, more readable format
    readable_id = f"{timestamp[-6:]}-{random_part[:6]}"
    
    return readable_id, unique_id

# System Prompt
SYSTEM_PROMPT = (
    "You are a professional job interviewer conducting a structured interview for a managerial position. "
    "Your goal is to assess the candidate's level of narcissism (grandiose narcissism and vulnerable narcissism) through engaging conversation. "
    "Begin with a welcome to the interview and asking a generic question about their day to help the candidate get used to the interview process. "
    "Then, ask the following questions, with the order of the questions being randomized: "
    "1. Do you consider yourself a natural born leader or someone who's had to learn how to lead? Provide an example of your leadership approach."
    "2. Imagine you are working on a team that requires unanimous consent to move forward on a project. The other members have agreed upon a plan for the project that you strongly disagree with. How do you proceed?"
    "3. Imagine you are the leader of a group and someone on your team openly expressed their concern with one of your decisions to you and others. It turns out that your decision was the correct call. How would you handle this situation?"
    "Ask questions in a friendly but authoritative tone. Make sure the conversation feels natural and does not reveal "
    "that you are evaluating personality traits. Always encourage detailed responses. "
    "If respondents ask for clarification, provide the following message: 'I'm instructed to follow a highly structured format and am limited from paraphrasing questions, providing explanations of questions, or probing. Please answer the question as you understand it.'\n\n"
    "IMPORTANT: You must ALWAYS respond with valid JSON in the following format:\n"
    "{\n"
    '  "response": "your conversational response here",\n'
    '  "question_asked": <number 0-3 or null>,\n'
    '  "is_clarification": <true or false>\n'
    "}\n"
    "Use question_asked values: 0 for generic day question, 1 for leadership question, 2 for team disagreement question, 3 for team concern question, null for other responses.\n"
    "Set is_clarification to true only when you are repeating/clarifying a question, false otherwise."
)

# Scoring Prompt for Grandiose Narcissism
SCORING_PROMPT = (
    "You are a psychological evaluator trained to assess grandiose narcissism in job candidates based on their interview responses. "
    "You will read a transcript of a simulated employment interview and assign a score that reflects the candidate's level of grandiose narcissism. "
    "This includes the overall grandiose narcissism trait, as well as its subfacets: Indifference, Exhibitionism, Authoritativeness, Grandiose Fantasies, Manipulativeness, Exploitativeness, Entitlement, Lack of empathy, Arrogance, Acclaim seeking, and Thrill seeking.\n\n"
    "The score should be on a five-point scale ranging between 1 (being low) and 5 (being high).\n\n"
    "Please provide your assessment in the following JSON format:\n"
    "{\n"
    '  "overall_score": <1-5>,\n'
    '  "indifference": <1-5>,\n'
    '  "exhibitionism": <1-5>,\n'
    '  "authoritativeness": <1-5>,\n'
    '  "grandiose_fantasies": <1-5>,\n'
    '  "manipulativeness": <1-5>,\n'
    '  "exploitativeness": <1-5>,\n'
    '  "entitlement": <1-5>,\n'
    '  "lack_of_empathy": <1-5>,\n'
    '  "arrogance": <1-5>,\n'
    '  "acclaim_seeking": <1-5>,\n'
    '  "thrill_seeking": <1-5>,\n'
    '  "explanation": "<brief explanation of the overall score>"\n'
    "}"
)

# File to store conversations
CONVERSATIONS_FILE = "conversations.json"

def load_conversations():
    """Load conversations from JSON file"""
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading conversations: {e}")
        return {}

def save_conversations(conversations):
    """Save conversations to JSON file"""
    try:
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump(conversations, f, indent=2)
    except Exception as e:
        print(f"Error saving conversations: {e}")

# Load existing conversations
user_sessions = load_conversations()

def chat_with_gpt(conversation_history):
    """Function to interact with OpenAI API"""
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please add OPENAI_API_KEY to Railway environment variables."
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o as gpt-5 might not be available yet
            messages=conversation_history,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Chat API Error: {str(e)}")
        return f"Error: {str(e)}"

def score_interview(conversation_history):
    """Function to score interview responses for grandiose narcissism"""
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please add OPENAI_API_KEY to Railway environment variables."
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Create the scoring conversation
        scoring_messages = [
            {"role": "system", "content": SCORING_PROMPT},
            {"role": "user", "content": f"Please evaluate the following interview transcript for grandiose narcissism:\n\n{conversation_history}"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o as gpt-5 might not be available yet
            messages=scoring_messages,
            max_tokens=1000,
            temperature=0.1  # Lower temperature for more consistent scoring
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Scoring API Error: {str(e)}")
        return f"Error: {str(e)}"

# ChatGPT-style HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background-color: #343541;
            color: #ececf1;
            height: 100vh;
            overflow: hidden;
        }
        
        .app-container {
            display: flex;
            height: 100vh;
        }
        
        .sidebar {
            width: 260px;
            background-color: #202123;
            border-right: 1px solid #4a4b53;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid #4a4b53;
        }
        
        .sidebar-title {
            font-size: 18px;
            font-weight: 600;
            color: #ececf1;
        }
        
        .new-chat-btn {
            width: calc(100% - 40px);
            padding: 12px 16px;
            background-color: #343541;
            border: 1px solid #565869;
            border-radius: 6px;
            color: #ececf1;
            font-size: 14px;
            cursor: pointer;
            margin: 10px 20px;
            transition: background-color 0.2s;
        }
        
        .new-chat-btn:hover {
            background-color: #40414f;
        }
        
        .instructions {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            font-size: 13px;
            line-height: 1.5;
            color: #c5c5d2;
        }
        
        .instructions h3 {
            font-size: 16px;
            font-weight: 600;
            color: #ececf1;
            margin-bottom: 10px;
        }
        
        .instructions h4 {
            font-size: 14px;
            font-weight: 600;
            color: #ececf1;
            margin-top: 16px;
            margin-bottom: 8px;
        }
        
        .instructions p {
            margin-bottom: 8px;
        }
        
        .instructions ul {
            margin-left: 16px;
            margin-bottom: 12px;
        }
        
        .instructions li {
            margin-bottom: 6px;
        }
        
        .instructions strong {
            color: #ececf1;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            padding: 20px;
            border-bottom: 1px solid #4a4b53;
            text-align: center;
        }
        
        .chat-title {
            font-size: 20px;
            font-weight: 600;
            color: #ececf1;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 0;
        }
        
        .message-group {
            border-bottom: 1px solid #4a4b53;
        }
        
        .message {
            padding: 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
        }
        
        .message-avatar {
            width: 30px;
            height: 30px;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            flex-shrink: 0;
        }
        
        .ai-avatar {
            background-color: #10a37f;
            color: white;
        }
        
        .user-avatar {
            background-color: #ececf1;
            color: #343541;
        }
        
        .message-content {
            flex: 1;
            line-height: 1.6;
            font-size: 16px;
        }
        
        .ai-message .message-content {
            color: #ececf1;
        }
        
        .user-message .message-content {
            color: #ececf1;
        }
        
        .message-content a {
            color: #10a37f;
            text-decoration: underline;
        }
        
        .input-container {
            padding: 20px;
            border-top: 1px solid #4a4b53;
            background-color: #343541;
        }
        
        .input-wrapper {
            max-width: 768px;
            margin: 0 auto;
            position: relative;
        }
        
        .message-input {
            width: 100%;
            padding: 12px 45px 12px 16px;
            background-color: #40414f;
            border: 1px solid #565869;
            border-radius: 6px;
            color: #ececf1;
            font-size: 16px;
            resize: none;
            min-height: 52px;
            max-height: 200px;
            outline: none;
            font-family: inherit;
        }
        
        .message-input:focus {
            border-color: #10a37f;
        }
        
        .send-btn {
            position: absolute;
            right: 8px;
            bottom: 8px;
            background-color: #10a37f;
            border: none;
            border-radius: 4px;
            width: 32px;
            height: 32px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            transition: background-color 0.2s;
        }
        
        .send-btn:hover {
            background-color: #0d8a6f;
        }
        
        .send-btn:disabled {
            background-color: #565869;
            cursor: not-allowed;
        }
        
        .start-btn {
            padding: 12px 24px;
            background-color: #10a37f;
            border: none;
            border-radius: 6px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin: 20px;
            transition: background-color 0.2s;
        }
        
        .start-btn:hover {
            background-color: #0d8a6f;
        }
        
        .start-btn:disabled {
            background-color: #565869;
            cursor: not-allowed;
        }
        
        .typing {
            padding: 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            color: #ececf1;
            font-style: italic;
        }
        
        .typing-avatar {
            width: 30px;
            height: 30px;
            background-color: #10a37f;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status {
            text-align: center;
            padding: 10px;
            background-color: #40414f;
            color: #ececf1;
            font-size: 14px;
            border-bottom: 1px solid #4a4b53;
        }
        
        .debug {
            display: none;
            background-color: #202123;
            padding: 10px;
            margin: 10px;
            border-radius: 4px;
            font-size: 12px;
            color: #ececf1;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #343541;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #565869;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #6b6c7b;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">Interview Chatbot</div>
            </div>
            <button class="new-chat-btn" onclick="startInterview()">🚀 Start Interview</button>
            <button class="new-chat-btn" onclick="clearChat()">🗑️ Clear Chat</button>
            
            <div class="instructions">
                <h3>Interview Instructions</h3>
                
                <h4>Welcome to the AI Interview Study</h4>
                <p>This is a simulated job interview designed to test the validity of AI-conducted interviews. Your participation will help us understand how well AI can assess candidates in an interview setting.</p>
                
                <h4>What to Expect</h4>
                <ul>
                    <li>The interview begins with a brief warm-up question to help you get comfortable</li>
                    <li>You will be asked <strong>3 questions</strong> about your leadership experience and decision-making approach</li>
                    <li>Answer each question thoughtfully and provide specific examples when possible</li>
                    <li><strong>Note:</strong> The interviewer follows a highly structured format and cannot paraphrase questions, provide explanations, or probe for more detail</li>
                </ul>
                
                <h4>Important Limits</h4>
                <ul>
                    <li><strong>Time Limit:</strong> 20 minutes from when the interview starts</li>
                    <li><strong>Message Limit:</strong> Maximum of 20 exchanges to ensure focused responses</li>
                    <li>The interview will end automatically when all questions are answered or when a limit is reached</li>
                </ul>
                
                <h4>After the Interview</h4>
                <p>Once you complete the interview, you will receive a <strong>unique ID</strong> and a link to a follow-up questionnaire. Please save your ID - you'll need it to match your interview responses with the questionnaire.</p>
                
                <h4>Tips for Success</h4>
                <ul>
                    <li>Be authentic and specific in your responses</li>
                    <li>Use real examples from your experience when possible</li>
                    <li>Take your time to think through your answers</li>
                    <li>There are no right or wrong answers - we want to hear your perspective</li>
                </ul>
                
                <p style="margin-top: 16px;"><strong>Click "Start Interview" when you're ready to begin.</strong></p>
            </div>
        </div>
        
        <div class="main-content">
            <div class="status" id="status">
                Ready to start your interview
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="message-group">
                    <div class="message ai-message">
                        <div class="message-avatar ai-avatar">AI</div>
                        <div class="message-content">
                            Welcome! I'm your AI interviewer. Click "Start Interview" to begin your practice session.
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="input-container">
                <div class="input-wrapper">
                    <textarea 
                        id="messageInput" 
                        class="message-input" 
                        placeholder="Type your response here..." 
                        onkeypress="handleKeyPress(event)"
                        rows="1"
                        disabled
                    ></textarea>
                    <button class="send-btn" onclick="sendMessage()" id="sendBtn" disabled>→</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="debug" id="debug"></div>

    <script>
        let currentUserId = 'web_user_' + Date.now();
        let isInterviewStarted = false;
        let answeredQuestions = new Set();
        let lastQuestionAsked = null;
        let isInterviewComplete = false;
        let totalMessageCount = 0;
        let interviewStartTime = null;
        let interviewTimeout = null;
        
        const MAX_MESSAGES = 20;
        const TIMEOUT_MINUTES = 20;

        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }

        function addMessage(content, isAI = false) {
            const chatContainer = document.getElementById('chatContainer');
            const messageGroup = document.createElement('div');
            messageGroup.className = 'message-group';
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isAI ? 'ai-message' : 'user-message'}`;
            
            const avatar = document.createElement('div');
            avatar.className = `message-avatar ${isAI ? 'ai-avatar' : 'user-avatar'}`;
            avatar.textContent = isAI ? 'AI' : 'You';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            messageGroup.appendChild(messageDiv);
            chatContainer.appendChild(messageGroup);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function addMessageHTML(content, isAI = false) {
            const chatContainer = document.getElementById('chatContainer');
            const messageGroup = document.createElement('div');
            messageGroup.className = 'message-group';
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isAI ? 'ai-message' : 'user-message'}`;
            
            const avatar = document.createElement('div');
            avatar.className = `message-avatar ${isAI ? 'ai-avatar' : 'user-avatar'}`;
            avatar.textContent = isAI ? 'AI' : 'You';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.innerHTML = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            messageGroup.appendChild(messageDiv);
            chatContainer.appendChild(messageGroup);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showTyping() {
            const chatContainer = document.getElementById('chatContainer');
            const messageGroup = document.createElement('div');
            messageGroup.className = 'message-group';
            messageGroup.id = 'typing';
            
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing';
            
            const avatar = document.createElement('div');
            avatar.className = 'typing-avatar';
            avatar.textContent = 'AI';
            
            const content = document.createElement('div');
            content.textContent = 'AI is thinking...';
            
            typingDiv.appendChild(avatar);
            typingDiv.appendChild(content);
            messageGroup.appendChild(typingDiv);
            chatContainer.appendChild(messageGroup);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function hideTyping() {
            const typingGroup = document.getElementById('typing');
            if (typingGroup) {
                typingGroup.remove();
            }
        }

        async function startInterview() {
            if (isInterviewStarted) return;
            
            updateStatus('Starting interview...');
            showTyping();
            
            try {
                const response = await fetch('/start_interview', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ user_id: currentUserId })
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, true);
                isInterviewStarted = true;
                answeredQuestions.clear();
                lastQuestionAsked = data.question_asked;
                isInterviewComplete = false;
                totalMessageCount = 0;
                
                // Start the interview timer
                interviewStartTime = Date.now();
                interviewTimeout = setTimeout(() => {
                    endInterview('timeout');
                }, TIMEOUT_MINUTES * 60 * 1000);
                
                // Enable input
                document.getElementById('messageInput').disabled = false;
                document.getElementById('sendBtn').disabled = false;
                document.getElementById('messageInput').focus();
                updateStatus('Interview in progress - Type your responses below');
                
            } catch (error) {
                hideTyping();
                addMessage('Error starting interview. Please try again.', true);
                updateStatus('Error starting interview');
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !isInterviewStarted || isInterviewComplete) return;
            
            // Check message limit
            totalMessageCount++;
            if (totalMessageCount > MAX_MESSAGES) {
                endInterview('message_limit');
                return;
            }
            
            // Add user message
            addMessage(message, false);
            input.value = '';
            
            showTyping();
            updateStatus('AI is responding...');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        user_id: currentUserId, 
                        message: message 
                    })
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, true);
                
                // Track which question was just asked and if previous was answered
                if (lastQuestionAsked !== null && !data.is_clarification) {
                    // User just answered the last question asked
                    answeredQuestions.add(lastQuestionAsked);
                }
                
                // Update last question asked
                if (data.question_asked !== null) {
                    lastQuestionAsked = data.question_asked;
                }
                
                // Check if all 4 questions have been answered (0, 1, 2, 3)
                if (answeredQuestions.size >= 4) {
                    endInterview('complete');
                } else {
                    const questionsRemaining = 4 - answeredQuestions.size;
                    const messagesRemaining = MAX_MESSAGES - totalMessageCount;
                    updateStatus(`Interview in progress - ${questionsRemaining} questions remaining (${messagesRemaining} messages left)`);
                }
                
            } catch (error) {
                hideTyping();
                addMessage('Error sending message. Please try again.', true);
                updateStatus('Error sending message');
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function endInterview(reason) {
            if (isInterviewComplete) return;
            
            isInterviewComplete = true;
            document.getElementById('messageInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
            
            // Clear the timeout
            if (interviewTimeout) {
                clearTimeout(interviewTimeout);
                interviewTimeout = null;
            }
            
            // Show appropriate completion message based on reason
            let statusMessage = '';
            let chatMessage = '';
            
            if (reason === 'complete') {
                statusMessage = 'Interview complete - Thank you for your responses!';
                chatMessage = 'Thank you for completing all the interview questions!';
            } else if (reason === 'timeout') {
                statusMessage = 'Interview ended - Time limit reached';
                chatMessage = 'The interview has ended due to the 20-minute time limit. Thank you for your responses.';
            } else if (reason === 'message_limit') {
                statusMessage = 'Interview ended - Message limit reached';
                chatMessage = 'The interview has ended due to the message limit. Thank you for your responses.';
            }
            
            updateStatus(statusMessage);
            if (chatMessage) {
                addMessage(chatMessage, true);
            }
            
            // Show completion message with unique ID
            showCompletionMessage();
        }

        function clearChat() {
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = `
                <div class="message-group">
                    <div class="message ai-message">
                    <div class="message-avatar ai-avatar">AI</div>
                    <div class="message-content">
                        Welcome! I'm your AI interviewer. Click "Start Interview" to begin your practice session.
                    </div>
                </div>
            `;
            
            // Clear timeout if active
            if (interviewTimeout) {
                clearTimeout(interviewTimeout);
                interviewTimeout = null;
            }
            
            // Reset all state variables
            currentUserId = 'web_user_' + Date.now();
            isInterviewStarted = false;
            isInterviewComplete = false;
            answeredQuestions.clear();
            lastQuestionAsked = null;
            totalMessageCount = 0;
            interviewStartTime = null;
            
            document.getElementById('messageInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
            updateStatus('Chat cleared - Ready to start new interview');
        }

        async function showCompletionMessage() {
            try {
                const response = await fetch('/get_unique_id', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ user_id: currentUserId })
                });
                
                const data = await response.json();
                
                if (data.unique_id) {
                    // Google Forms survey link for post-interview questionnaire
                    const survey_url = "https://docs.google.com/forms/d/e/1FAIpQLSebDBBQQr0naKWatJd8fEUVsrfKKWBnFlEBq97LEMjl3l9CHg/viewform?usp=publish-editor";
                    const completionMessageHTML = `
                        <div>Thanks for completing the interview!</div>
                        <div style="margin-top:8px;">Please now complete the self-report questionnaire here:
                            <br><a href="${survey_url}" target="_blank" rel="noopener noreferrer">Open the self-report questionnaire</a>
                        </div>
                        <div style="margin-top:12px;"><strong>Your unique user ID:</strong></div>
                        <div><code style="font-size:16px; padding:2px 6px; background:#2b2c36; border-radius:4px;">${data.unique_id}</code></div>
                    `;
                    addMessageHTML(completionMessageHTML, true);
                } else {
                    addMessage("Thank you for completing the interview! Your responses have been recorded.", true);
                }
                
            } catch (error) {
                addMessage("Thank you for completing the interview! Your responses have been recorded.", true);
            }
        }

        function openSurvey() {
            // This will be updated when the survey is ready
            alert('Survey link will be available soon. Please save your unique code for later use.');
        }

        // Auto-resize textarea
        document.addEventListener('DOMContentLoaded', function() {
            const textarea = document.getElementById('messageInput');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 200) + 'px';
            });
        });
    </script>
</body>
</html>
"""

@app.route('/health', methods=['GET'])
def health():
    """Minimal health/status endpoint to verify service and env configuration."""
    try:
        key_present = bool(OPENAI_API_KEY)
    except Exception:
        key_present = False
    return jsonify({
        "status": "ok",
        "openai_key_present": key_present
    })

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_interview', methods=['POST'])
def start_interview():
    print("Start interview endpoint called")
    user_id = request.json.get("user_id")
    print(f"User ID: {user_id}")

    if user_id not in user_sessions:
        user_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Generate and store unique identifier for this session
        readable_id, unique_id = generate_unique_id()
        user_sessions[user_id].append({"role": "system", "content": f"UNIQUE_ID: {unique_id}"})
        user_sessions[user_id].append({"role": "system", "content": f"READABLE_ID: {readable_id}"})

    # Follow the system prompt structure: welcome + generic question
    welcome_data = {
        "response": "Welcome to your interview! I'm excited to have this conversation with you today. How are you doing today?",
        "question_asked": 0,
        "is_clarification": False
    }
    welcome_message_json = json.dumps(welcome_data)
    user_sessions[user_id].append({"role": "assistant", "content": welcome_message_json})
    
    # Save conversations after starting interview
    save_conversations(user_sessions)
    print("Interview started successfully")

    return jsonify(welcome_data)

@app.route('/chat', methods=['POST'])
def chat():
    print("Chat endpoint called")
    user_id = request.json.get("user_id")
    user_message = request.json.get("message")
    print(f"User ID: {user_id}, Message: {user_message}")

    if user_id not in user_sessions:
        user_sessions[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    conversation = user_sessions[user_id]
    conversation.append({"role": "user", "content": user_message})
    
    print(f"Conversation history: {conversation}")
    print("Calling GPT API...")
    
    response_message = chat_with_gpt(conversation)
    print(f"AI Response: {response_message}")

    conversation.append({"role": "assistant", "content": response_message})
    
    # Save conversations after each interaction
    save_conversations(user_sessions)

    # Parse JSON response from GPT
    try:
        response_data = json.loads(response_message)
        return jsonify(response_data)
    except json.JSONDecodeError:
        # Fallback if GPT doesn't return valid JSON
        print(f"Warning: GPT response was not valid JSON: {response_message}")
        return jsonify({
            "response": response_message,
            "question_asked": None,
            "is_clarification": False
        })

@app.route('/score_interview', methods=['POST'])
def score_interview_endpoint():
    print("Score interview endpoint called")
    user_id = request.json.get("user_id")
    print(f"User ID: {user_id}")

    if user_id not in user_sessions:
        return jsonify({"error": "No interview found for this user"}), 400

    conversation = user_sessions[user_id]
    
    # Convert conversation to readable format for scoring
    conversation_text = ""
    for message in conversation:
        if message["role"] != "system":  # Exclude system prompt
            role = "Interviewer" if message["role"] == "assistant" else "Candidate"
            conversation_text += f"{role}: {message['content']}\n\n"
    
    # Score the interview
    scoring_result = score_interview(conversation_text)
    print(f"Scoring Result: {scoring_result}")
    
    return jsonify({"scoring_result": scoring_result})

@app.route('/get_unique_id', methods=['POST'])
def get_unique_id():
    print("Get unique ID endpoint called")
    user_id = request.json.get("user_id")
    print(f"User ID: {user_id}")

    if user_id not in user_sessions:
        return jsonify({"error": "No interview found for this user"}), 400

    conversation = user_sessions[user_id]
    
    # Find the unique identifier in the conversation
    unique_id = None
    for message in conversation:
        if message["role"] == "system" and message["content"].startswith("READABLE_ID:"):
            unique_id = message["content"].replace("READABLE_ID:", "").strip()
            break
    
    if unique_id:
        return jsonify({"unique_id": unique_id})
    else:
        return jsonify({"error": "Unique ID not found"}), 404

@app.route('/export_mapping', methods=['GET'])
def export_mapping():
    """Export the mapping between unique IDs and user sessions for research purposes"""
    print("Export mapping endpoint called")
    
    mapping = {}
    for user_id, conversation in user_sessions.items():
        unique_id = None
        readable_id = None
        
        for message in conversation:
            if message["role"] == "system" and message["content"].startswith("UNIQUE_ID:"):
                unique_id = message["content"].replace("UNIQUE_ID:", "").strip()
            elif message["role"] == "system" and message["content"].startswith("READABLE_ID:"):
                readable_id = message["content"].replace("READABLE_ID:", "").strip()
        
        if unique_id and readable_id:
            mapping[readable_id] = {
                "unique_id": unique_id,
                "user_id": user_id,
                "message_count": len([m for m in conversation if m["role"] != "system"])
            }
    
    return jsonify(mapping)

if __name__ == '__main__':
    print(f"Starting Interview Chatbot on {config['host']}:{config['port']}")
    print(f"Debug mode: {config['debug']}")
    app.run(host=config['host'], port=config['port'], debug=config['debug']) 