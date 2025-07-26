import streamlit as st
import pandas as pd
import numpy as np
import random
from PIL import Image
import PyPDF2
import pdfplumber
import re
import os
import plotly.express as px
from datetime import datetime
import json

# Initialize database
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine('sqlite:///quiz_db.db')
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    score = Column(Integer, default=0)
    last_quiz_date = Column(DateTime)

class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    question = Column(String(500))
    option_a = Column(String(200))
    option_b = Column(String(200))
    option_c = Column(String(200))
    option_d = Column(String(200))
    correct_answer = Column(String(1))
    image_url = Column(String(200))
    source = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

class Newsletter(Base):
    __tablename__ = 'newsletters'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)  # Key points/summary
    content = Column(Text, nullable=False)  # Full content
    image_url = Column(String(500))
    source_url = Column(String(500))  # New field for storing the source URL
    date_published = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Integer, default=1)  # 1 for published, 0 for draft
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(engine)

# Initialize session
Session = sessionmaker(bind=engine)
session = Session()

# Initialize session state
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.is_admin = False  # Flag to check if user is admin
if 'quiz_source' not in st.session_state:
    st.session_state.quiz_source = None

def extract_questions_from_pdf(pdf_file):
    """Extract questions and answers from a PDF quiz."""
    st.subheader("🔍 Extracting Quiz Questions")
    
    questions = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Extract all text from all pages
            full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
            
            # Split text into lines and clean up
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            current_question = None
            current_options = {}
            current_answers = []
            
            # Patterns to match questions and options
            question_pattern = re.compile(r'^(\d+)\.\s+(.+)$')
            option_pattern = re.compile(r'^([a-d])\)\s+(.+)$', re.IGNORECASE)
            answer_pattern = re.compile(r'^Answer:\s*([a-d])$', re.IGNORECASE)
            
            for line in lines:
                # Check if line is a question
                q_match = question_pattern.match(line)
                if q_match:
                    # Save previous question if exists
                    if current_question and current_options:
                        questions.append({
                            'question': current_question,
                            'options': current_options,
                            'answer': current_answers[0] if current_answers else None
                        })
                    current_question = q_match.group(2)
                    current_options = {}
                    current_answers = []
                
                # Check if line is an option
                opt_match = option_pattern.match(line)
                if opt_match and current_question:
                    letter = opt_match.group(1).lower()
                    current_options[letter] = opt_match.group(2)
                
                # Check if line is an answer
                ans_match = answer_pattern.match(line)
                if ans_match and current_question and current_options:
                    current_answers.append(ans_match.group(1).lower())
            
            # Add the last question if it exists
            if current_question and current_options:
                questions.append({
                    'question': current_question,
                    'options': current_options,
                    'answer': current_answers[0] if current_answers else None
                })
            
            # Convert to the format expected by the rest of the application
            formatted_questions = []
            for q in questions:
                formatted_question = {
                    'question': q['question'],
                    'options': q['options'],
                    'answer': q['answer']
                }
                formatted_questions.append(formatted_question)
            
            # Display extracted questions
            if formatted_questions:
                st.success(f"✅ Successfully extracted {len(formatted_questions)} questions!")
                for i, q in enumerate(formatted_questions, 1):
                    with st.expander(f"Question {i}", expanded=i==1):
                        st.write(f"**{q['question']}**")
                        for letter, text in q['options'].items():
                            st.write(f"{letter}) {text}")
                        if q['answer']:
                            st.success(f"Answer: {q['answer']}")
                        else:
                            st.warning("No answer found for this question")
                return formatted_questions
            else:
                st.warning("No questions found in the PDF.")
                return []
                
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        st.error("Please ensure the PDF contains properly formatted quiz questions.")
        return []
    
    except Exception as e:
        st.error(f"Error analyzing PDF: {str(e)}")
        st.error("""
        Possible issues:
        1. PDF is password protected
        2. PDF is corrupted
        3. PDF contains only images (no text layer)
        4. File is not a valid PDF
        """)
    
    # Show instructions for the user
    st.subheader("❓ How to Proceed")
    st.markdown("""
    Based on the analysis above:
    
    1. If you see your text content:
       - The PDF is being read but we need to adjust the parsing
       - Please share a sample of how your questions are formatted
    
    2. If you see "No text found" or mostly empty results:
       - Your PDF might be image-based (scanned document)
       - We'll need to use OCR to extract the text
    
    3. If you see error messages:
       - The PDF might be corrupted or have an unusual format
       - Try opening it in a PDF viewer to verify it's not damaged
    
    **Please share a sample of how your questions are formatted in the PDF**
    """)
    
    return []  # Return empty list since we're just analyzing
    
    # Add the last question if it exists
    if current_question and len(current_options) == 4:
        questions.append({
            'question': f"{current_question_number}. {current_question}",
            'options': current_options
        })
        st.write(f"- Added final question: {current_question_number}. {current_question}")
    
    # If no questions found, try alternative method using character positions
    if not questions:
        st.write("\nNo questions found with text extraction. Trying alternative method...")
        
        # Try to extract using character positions
        st.write("\nProcessing pages with character positions:")
        for page_num, page in enumerate(pdf.pages, 1):
            st.write(f"\nPage {page_num}:")
            
            # Get all characters with their positions
            chars = page.chars
            if not chars:
                st.write(f"- No characters found on page {page_num}")
                continue
                
            st.write(f"- Found {len(chars)} characters with positions")
            
            # Process characters by their positions
            current_question_text = ""
            current_question_number = None
            current_options_text = {}
            current_question_type = None
            
            # Group characters by their vertical position
            lines = {}
            for char in chars:
                y_pos = round(char['top'], 1)
                if y_pos not in lines:
                    lines[y_pos] = []
                lines[y_pos].append(char)
            
            # Process each line
            for y_pos in sorted(lines.keys()):
                line_chars = sorted(lines[y_pos], key=lambda x: x['x0'])
                line_text = ''.join(char['text'] for char in line_chars)
                
                # Check if this line is a question
                is_question = False
                for pattern in question_patterns:
                    if re.match(pattern, line_text):
                        is_question = True
                        break
                
                # Check if this line is an option
                is_option = False
                for pattern in option_patterns:
                    if re.match(pattern, line_text):
                        is_option = True
                        break
                
                if is_question:
                    st.write(f"- Found question: {line_text}")
                    
                    # If we have a complete question, add it
                    if current_question_text and len(current_options_text) == 4:
                        questions.append({
                            'question': f"{current_question_number}. {current_question_text}",
                            'options': current_options_text
                        })
                        st.write(f"  Added question: {current_question_number}. {current_question_text}")
                    
                    # Start new question
                    current_question_number = line_text.split('.')[0].strip()
                    current_question_text = line_text.split('.')[-1].strip()
                    current_options_text = {}
                    current_question_type = 'MCQ'
                    st.write(f"  New question started: {current_question_number}. {current_question_text}")
                
                # If we're in a question and haven't found options yet
                elif current_question_text and not current_options_text:
                    # If this line is an option
                    if is_option:
                        st.write(f"- Found option: {line_text}")
                        
                        # Extract option letter and text
                        option_letter = line_text[0]  # Get the first character
                        option_text = line_text[1:].strip()  # Get the rest of the line
                        
                        if option_letter and option_text:
                            # Convert single letter to string key
                            option_key = str(option_letter)
                            current_options_text[option_key] = option_text
                            st.write(f"  Added option {option_key}: {option_text}")
                        
                        # If we have all 4 options, add the question
                        if len(current_options_text) == 4:
                            questions.append({
                                'question': f"{current_question_number}. {current_question_text}",
                                'options': current_options_text
                            })
                            st.write(f"  Complete question added: {current_question_number}. {current_question_text}")
                            current_question_text = None
                            current_options_text = {}
                            current_question_number = None
                            current_question_type = None
                    
                    # If this line is not an option, add it to question text
                    else:
                        current_question_text += f" {line_text}"
                        st.write(f"  Added to question: {line_text}")
                
                # If we're not in a question but found an option
                elif is_option:
                    st.write(f"- Found option without question: {line_text}")
                    st.write("  Skipping orphaned option")
    
    # Show final results
    st.write("\nFinal Results:")
    st.write(f"Total questions found: {len(questions)}")
    for idx, q in enumerate(questions, 1):
        st.write(f"\nQuestion {idx}:")
        st.write(f"- {q['question']}")
        for opt in q['options'].values():
            st.write(f"- {opt}")
    
    return questions

def create_quiz_from_pdf(uploaded_file):
    try:
        questions = extract_questions_from_pdf(uploaded_file)
        
        if not questions:
            raise ValueError("No questions found in the PDF. Please ensure the PDF contains quiz questions in the correct format.")
            
        # Create a temporary dictionary to store questions and their correct answers
        temp_questions = []
        for q in questions:
            temp_questions.append({
                'question': q['question'],
                'options': q['options'],
                'correct_answer': 'A'  # Default to A
            })
        
        # Show extracted questions for review
        st.subheader("Extracted Questions")
        for idx, q in enumerate(temp_questions):
            with st.expander(f"Question {idx + 1}"):
                st.write(q['question'])
                for opt in q['options'].values():
                    st.write(f"- {opt}")
                
                # Allow user to select correct answer
                q['correct_answer'] = st.selectbox(
                    "Select correct answer",
                    ['A', 'B', 'C', 'D'],
                    index=0,  # Default to A
                    key=f"correct_{idx}"
                )
        
        # Add to database
        if st.button("Save Questions"):
            for q in temp_questions:
                new_quiz = Quiz(
                    question=q['question'],
                    option_a=q['options']['A'],
                    option_b=q['options']['B'],
                    option_c=q['options']['C'],
                    option_d=q['options']['D'],
                    correct_answer=q['correct_answer'],
                    source=uploaded_file.name,
                    created_at=datetime.utcnow()
                )
                session.add(new_quiz)
            session.commit()
            st.success(f"Successfully added {len(temp_questions)} questions to the quiz!")
        
        return temp_questions
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return []

# Sample quiz questions (you can expand this list)
quiz_questions = [
    {
        'question': 'What is the main difference between supervised and unsupervised learning?',
        'options': {
            'A': 'Supervised learning requires labeled data, unsupervised does not',
            'B': 'Unsupervised learning requires labeled data, supervised does not',
            'C': 'There is no difference',
            'D': 'Supervised learning is faster than unsupervised'
        },
        'correct': 'A',
        'image_url': 'https://via.placeholder.com/400x300',
        'source': 'Introduction to ML'
    },
    {
        'question': 'Which algorithm is commonly used for image recognition?',
        'options': {
            'A': 'K-means clustering',
            'B': 'Linear regression',
            'C': 'Convolutional Neural Networks',
            'D': 'Decision Trees'
        },
        'correct': 'C',
        'image_url': 'https://via.placeholder.com/400x300',
        'source': 'Deep Learning Basics'
    }
]

# Sample newsletter content
newsletter_content = [
    {
        'title': 'AI in Healthcare: Latest Breakthroughs',
        'date': '2025-07-26',
        'content': '''
        Recent advancements in AI have revolutionized healthcare diagnostics. 
        Deep learning models are now achieving human-level accuracy in medical imaging analysis.
        ''',
        'image': 'https://via.placeholder.com/400x300',
        'sources': [
            'Nature Medicine',
            'IEEE Spectrum',
            'Journal of Medical AI'
        ]
    },
    {
        'title': 'Understanding JARVIS: AI in Movies',
        'date': '2025-07-25',
        'content': '''
        Iron Man's JARVIS system is a perfect example of how AI can be integrated into daily life. 
        This article breaks down the real-world technologies that inspired JARVIS and how they're being implemented today.
        ''',
        'image': 'https://via.placeholder.com/400x300',
        'sources': [
            'IEEE Spectrum',
            'AI Magazine',
            'TechCrunch'
        ]
    }
]

def show_create_quiz():
    st.header("Create Quiz")
    
    # Store questions in session state if not already present
    if 'extracted_questions' not in st.session_state:
        st.session_state.extracted_questions = []
    
    # File uploader for PDF
    uploaded_file = st.file_uploader("Upload a PDF containing quiz questions", type=['pdf'])
    
    if uploaded_file is not None:
        try:
            # Create quiz from PDF
            with st.spinner('Creating quiz from PDF...'):
                questions = extract_questions_from_pdf(uploaded_file)
                if questions:
                    st.session_state.extracted_questions = questions
                    st.success(f"Successfully created {len(questions)} quiz questions!")
                    
                    # Show sample questions
                    st.subheader("Review Questions")
                    for i, q in enumerate(questions):
                        with st.expander(f"Question {i+1}", expanded=i<2):
                            st.write(f"**{q['question']}**")
                            for letter, text in q['options'].items():
                                st.write(f"{letter.upper()}) {text}")
                            if q.get('answer'):
                                st.success(f"Correct Answer: {q['answer'].upper()}")
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
    
    # Show save section if we have extracted questions
    if st.session_state.extracted_questions:
        st.subheader("Save Quiz")
        quiz_title = st.text_input("Quiz Title", "AI/ML Quiz")
        quiz_description = st.text_area("Description", "A quiz about AI and Machine Learning")
        
        if st.button("Save Quiz"):
            try:
                # Add quiz to database
                for q in st.session_state.extracted_questions:
                    new_quiz = Quiz(
                        question=q['question'],
                        option_a=q['options'].get('a', ''),
                        option_b=q['options'].get('b', ''),
                        option_c=q['options'].get('c', ''),
                        option_d=q['options'].get('d', ''),
                        correct_answer=q.get('answer', 'A').upper(),
                        source=f"PDF: {uploaded_file.name if uploaded_file else 'Unknown'}"
                    )
                    session.add(new_quiz)
                
                session.commit()
                st.success(f"Successfully saved {len(st.session_state.extracted_questions)} questions to the database!")
                
                # Clear the extracted questions
                st.session_state.extracted_questions = []
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving quiz: {str(e)}")
                session.rollback()
    
    # Manual quiz creation
    st.subheader("Create Question Manually")
    
    with st.form("create_question"):
        question = st.text_area("Question", "")
        option_a = st.text_input("Option A", "")
        option_b = st.text_input("Option B", "")
        option_c = st.text_input("Option C", "")
        option_d = st.text_input("Option D", "")
        correct_answer = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
        image_url = st.text_input("Image URL (optional)", "")
        source = st.text_input("Source (optional)", "")
        
        if st.form_submit_button("Add Question"):
            if question and option_a and option_b and option_c and option_d:
                new_quiz = Quiz(
                    question=question,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=correct_answer,
                    image_url=image_url if image_url else None,
                    source=source if source else None
                )
                session.add(new_quiz)
                session.commit()
                st.success("Question added successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields")

def show_home():
    st.header("Welcome to AI/ML World")
    
    # Add some interactive elements
    st.subheader("Quick Quiz")
    st.write("""
    Test your knowledge with our quick quiz!
    """)
    
    # Create a form to handle the button click
    with st.form("start_quiz_form"):
        if st.form_submit_button("Start Quiz"):
            # Reset quiz state
            st.session_state.current_question = 0
            st.session_state.quiz_score = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_completed = False
            
            # Set flag to show quiz section
            st.session_state.show_quiz = True
            st.rerun()

def show_leaderboard():
    st.header("🏆 Leaderboard")
    
    # Add a refresh button
    if st.button("🔄 Refresh Leaderboard"):
        # Clear any cached data
        if 'leaderboard_data' in st.session_state:
            del st.session_state.leaderboard_data
        st.rerun()
    
    # Get top users with their rank
    if 'leaderboard_data' not in st.session_state:
        # Create a new session to ensure we get fresh data
        fresh_session = sessionmaker(bind=engine)()
        users = fresh_session.query(User).order_by(
            User.score.desc(), 
            User.last_quiz_date.desc()
        ).limit(10).all()
        fresh_session.close()
        st.session_state.leaderboard_data = users
    else:
        users = st.session_state.leaderboard_data
    
    # Create leaderboard data with rank
    leaderboard_data = []
    for rank, user in enumerate(users, 1):
        leaderboard_data.append({
            'Rank': rank,
            'Username': user.username,
            'Score': user.score,
            'Last Active': user.last_quiz_date.strftime('%Y-%m-%d') if user.last_quiz_date else 'Never',
            'Days Since Last Quiz': (datetime.utcnow() - user.last_quiz_date).days if user.last_quiz_date else float('inf')
        })
    
    if not leaderboard_data:
        st.info("No quiz results yet. Be the first to take the quiz!")
        return
    
    # Create DataFrame
    df = pd.DataFrame(leaderboard_data)
    
    # Highlight current user's row if logged in
    def highlight_user(row):
        if 'username' in st.session_state and row['Username'] == st.session_state.username:
            return ['background-color: #e6f3ff'] * len(row)
        return [''] * len(row)
    
    # Display styled table
    st.subheader("Top Performers")
    st.dataframe(
        df[['Rank', 'Username', 'Score', 'Last Active']].style.apply(highlight_user, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            'Rank': st.column_config.NumberColumn(width='small'),
            'Username': st.column_config.TextColumn(width='medium'),
            'Score': st.column_config.ProgressColumn(
                'Score',
                help='Total quiz score',
                format='%d',
                min_value=0,
                max_value=df['Score'].max() * 1.1  # 10% buffer for visual appeal
            ),
            'Last Active': st.column_config.DateColumn(
                'Last Active',
                format='YYYY-MM-DD',
                help='Last time the user took a quiz'
            )
        }
    )
    
    # Show additional stats if user is logged in
    if 'user_id' in st.session_state:
        user_rank = df[df['Username'] == st.session_state.username].index
        if not user_rank.empty:
            rank = user_rank[0] + 1
            user_score = df.loc[user_rank[0], 'Score']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Your Rank", f"#{rank} of {len(users)}")
            with col2:
                st.metric("Your Score", user_score)
            
            # Show progress to next rank if not first
            if rank > 1:
                if rank > 2:
                    score_to_next = df.loc[rank-2, 'Score'] - user_score + 1
                    st.progress(
                        min(1.0, user_score / (score_to_next + user_score)),
                        f"You need {score_to_next} more points to reach rank {rank-1}"
                    )
    
    # Create interactive bar chart
    st.subheader("Score Distribution")
    fig = px.bar(
        df.head(10),  # Show top 10
        x='Username',
        y='Score',
        color='Score',
        color_continuous_scale='Viridis',
        title='Top 10 Users by Score',
        labels={'Score': 'Total Score', 'Username': 'User'}
    )
    
    # Customize the chart
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title='Total Score',
        coloraxis_showscale=False,
        hovermode='x unified'
    )
    
    # Add horizontal line at average score if there are enough users
    if len(df) > 2:
        avg_score = df['Score'].mean()
        fig.add_hline(
            y=avg_score,
            line_dash='dash',
            line_color='red',
            annotation_text=f'Average: {avg_score:.1f}'
        )
    
    st.plotly_chart(fig, use_container_width=True)

def show_quiz():
    st.header("AI/ML Quiz")
    
    if not st.session_state.user_id:
        st.error("Please login to take the quiz")
        return
    
    # Initialize session state for quiz management
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    
    # Get all quizzes from database with debug info
    st.sidebar.subheader("Database Info")
    
    # Get all quiz questions - cache this to avoid repeated database queries
    if 'all_quizzes' not in st.session_state:
        st.session_state.all_quizzes = session.query(Quiz).all()
    
    all_quizzes = st.session_state.all_quizzes
    
    # Show database stats
    st.sidebar.write(f"Total questions in database: {len(all_quizzes)}")
    
    # Check for duplicates
    seen_questions = {}
    duplicates = []
    
    for quiz in all_quizzes:
        if quiz.question in seen_questions:
            duplicates.append((seen_questions[quiz.question], quiz.id))
        else:
            seen_questions[quiz.question] = quiz.id
    
    # Show duplicate info
    if duplicates:
        st.sidebar.warning(f"Found {len(duplicates)} duplicate questions in database")
        
        # Add button to clean duplicates
        if st.sidebar.button("Clean Duplicate Questions"):
            try:
                # Keep the first occurrence of each question
                for original_id, duplicate_id in duplicates:
                    session.query(Quiz).filter(Quiz.id == duplicate_id).delete()
                session.commit()
                st.session_state.all_quizzes = session.query(Quiz).all()  # Refresh cached quizzes
                st.sidebar.success(f"Removed {len(duplicates)} duplicate questions")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error removing duplicates: {e}")
                session.rollback()
    
    # Get unique questions for the quiz - cache this as well
    if 'quizzes' not in st.session_state:
        quizzes = []
        seen = set()
        for quiz in all_quizzes:
            if quiz.question not in seen:
                seen.add(quiz.question)
                quizzes.append(quiz)
        st.session_state.quizzes = quizzes
    
    quizzes = st.session_state.quizzes
    st.sidebar.write(f"Unique questions available: {len(quizzes)}")
    
    if not quizzes:
        st.warning("No quizzes available. Please create a quiz first.")
        return
    
    # Display quiz progress
    total_questions = len(quizzes)
    current_q = st.session_state.current_question
    st.write(f"Question {current_q + 1} of {total_questions}")
    progress = st.progress((current_q + 1) / total_questions)
    
    # Get current question
    quiz = quizzes[current_q]
    
    st.subheader(quiz.question)
    
    # Display image if available
    if quiz.image_url:
        st.image(quiz.image_url, caption="Question Image", use_container_width=True)
    
    # Display options
    options = {
        'A': quiz.option_a,
        'B': quiz.option_b,
        'C': quiz.option_c,
        'D': quiz.option_d
    }
    
    # Get or initialize user answer for current question
    user_answer = st.session_state.user_answers.get(current_q, '')
    
    # Create a form for the question to handle state properly
    with st.form(key=f'question_{current_q}'):
        # Display radio buttons for options
        selected_option = st.radio(
            "Select your answer",
            options=list(options.keys()),
            format_func=lambda x: f"{x}) {options[x]}",
            index=ord(user_answer) - ord('A') if user_answer and user_answer.upper() in 'ABCD' else 0
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            prev_button = st.form_submit_button("Previous Question", disabled=current_q == 0)
        
        with col2:
            if current_q < total_questions - 1:
                next_button = st.form_submit_button("Next Question")
            else:
                submit_button = st.form_submit_button("Submit Quiz")
    
    # Handle navigation
    if 'prev_button' in locals() and prev_button:
        st.session_state.user_answers[current_q] = selected_option
        st.session_state.current_question = max(0, current_q - 1)
        st.rerun()
    
    if 'next_button' in locals() and next_button:
        st.session_state.user_answers[current_q] = selected_option
        st.session_state.current_question = min(total_questions - 1, current_q + 1)
        st.rerun()
    
    if 'submit_button' in locals() and submit_button:
        st.session_state.user_answers[current_q] = selected_option
        
        # Calculate score
        score = 0
        for i, q in enumerate(quizzes):
            if str(st.session_state.user_answers.get(i, '')).upper() == q.correct_answer.upper():
                score += 1
        
        # Update user score
        try:
            # Start a new session to avoid any stale data
            new_session = sessionmaker(bind=engine)()
            user = new_session.query(User).filter_by(id=st.session_state.user_id).with_for_update().first()
            
            if user:
                # Calculate new score (add to existing score)
                new_score = user.score + score
                
                # Update user's score and last quiz date
                user.score = new_score
                user.last_quiz_date = datetime.utcnow()
                
                # Commit the changes
                new_session.commit()
                
                # Update session state
                st.session_state.quiz_score = score
                st.session_state.quiz_completed = True
                
                # Show success message
                st.toast(f"Score updated! You earned {score} points! Total score: {new_score}")
                
                # Clear any cached data that might be stale
                if 'all_quizzes' in st.session_state:
                    del st.session_state.all_quizzes
                if 'quizzes' in st.session_state:
                    del st.session_state.quizzes
                
                # Force a rerun to refresh the UI
                st.rerun()
                return
                
        except Exception as e:
            if 'new_session' in locals():
                new_session.rollback()
            st.error(f"Error updating score: {str(e)}")
            st.stop()
    
    # Display score if quiz is completed
    if st.session_state.get('quiz_completed', False):
        st.success(f"Quiz completed! Your score: {st.session_state.quiz_score}/{total_questions}")
        
        # Show correct answers
        st.subheader("Quiz Review:")
        for i, q in enumerate(quizzes):
            user_ans = st.session_state.user_answers.get(i, 'Not answered')
            is_correct = str(user_ans).upper() == q.correct_answer.upper()
            
            with st.expander(f"Question {i+1}: {q.question}", expanded=False):
                st.write(f"Your answer: {user_ans}) {options.get(user_ans, 'Not answered')}")
                st.write(f"Correct answer: {q.correct_answer}) {options.get(q.correct_answer.upper(), '')}")
                st.write("Correct!" if is_correct else "Incorrect")
        
        if st.button("Restart Quiz"):
            st.session_state.current_question = 0
            st.session_state.quiz_score = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_completed = False
            st.rerun()
        st.rerun()

def extract_article_from_url(url):
    """Extract article content from URL and return title, content, and metadata."""
    try:
        from newspaper import Article
        import requests
        from bs4 import BeautifulSoup
        
        # First try with newspaper3k
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # If we get a title but no content, try a different approach
            if article.title and (not article.text or len(article.text) < 50):
                raise Exception("Insufficient content from newspaper3k, trying alternative method")
                
            return {
                'title': article.title,
                'content': article.text,  # Store full content
                'summary': article.title,  # Use title as summary for display
                'image_url': article.top_image or url,  # Store source URL if no image
                'source_url': url  # Store the original URL
            }
            
        except Exception as e:
            st.warning(f"Newspaper3k extraction issue: {str(e)[:200]}...")
            
            # Fallback to requests + BeautifulSoup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get title from common meta tags
            title = ''
            for tag in ['og:title', 'twitter:title', 'title']:
                title_tag = soup.find('meta', property=tag) or soup.find('meta', {'name': tag})
                if title_tag and title_tag.get('content'):
                    title = title_tag['content']
                    break
            
            # If no title found in meta, try to get it from h1
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # If still no title, use the URL
            if not title:
                title = url
            
            # Get the first paragraph as summary
            summary = ''
            for p in soup.find_all('p'):
                if len(p.get_text(strip=True)) > 50:  # Only consider paragraphs with some content
                    summary = p.get_text(strip=True)
                    break
            
            return {
                'title': title,
                'content': title,  # Just use title as content for display
                'summary': summary[:200] + '...' if summary else title,
                'image_url': url,  # Store source URL as image_url
                'source_url': url  # Store the original URL
            }
            
    except Exception as e:
        st.error(f"Error extracting content from URL: {str(e)[:200]}...")
        return None

def show_newsletter():
    st.header("📰 AI/ML Newsletter")
    
    # Show admin notice
    if st.session_state.get('is_admin'):
        st.success("🔧 Admin Mode: You can add and edit newsletter items")
    
    # Admin can add new newsletter items
    if st.session_state.get('is_admin'):
        with st.expander("📝 Add New Newsletter Item", expanded=False):
            tab1, tab2 = st.tabs(["Manual Entry", "Extract from URL"])
            
            with tab1:
                with st.form(key='add_news_form'):
                    title = st.text_input("Title*")
                    summary = st.text_area("Key Points/Summary*", help="Enter the main points that users will see initially")
                    content = st.text_area("Full Content*", help="Enter the detailed content")
                    image_url = st.text_input("Image URL (optional)", placeholder="https://example.com/image.jpg")
                    source_url = st.text_input("Source URL (optional)", placeholder="https://example.com/original-article")
                    date_published = st.date_input("Publish Date", value=datetime.utcnow().date())
                    is_published = st.checkbox("Publish immediately", value=True)
                    
                    if st.form_submit_button("Save Newsletter Item"):
                        if title and summary and content:
                            try:
                                new_item = Newsletter(
                                    title=title,
                                    summary=summary,
                                    content=content,
                                    image_url=image_url if image_url else None,
                                    source_url=source_url if source_url else None,
                                    date_published=datetime.combine(date_published, datetime.min.time()),
                                    is_published=1 if is_published else 0
                                )
                                session.add(new_item)
                                session.commit()
                                st.success("Newsletter item saved successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving newsletter item: {e}")
                                session.rollback()
                        else:
                            st.error("Please fill in all required fields (marked with *)")
            
            with tab2:
                with st.form(key='extract_url_form'):
                    url = st.text_input("Article URL*", placeholder="https://example.com/article")
                    date_published = st.date_input("Publish Date", value=datetime.utcnow().date(), key='url_date')
                    is_published = st.checkbox("Publish immediately", value=True, key='url_publish')
                    
                    if st.form_submit_button("Extract and Save"):
                        if url:
                            with st.spinner("Extracting content from URL..."):
                                article = extract_article_from_url(url)
                                if article:
                                    try:
                                        # Store the source URL in the image_url field if no image is available
                                        source_url = article.get('source_url', url)
                                        image_url = article.get('image_url')
                                        if image_url == url:  # If image_url is the source URL, don't use it as an image
                                            image_url = None
                                            
                                        new_item = Newsletter(
                                            title=article['title'],
                                            summary=article.get('summary', article['title']),
                                            content=article['content'],
                                            image_url=image_url,
                                            source_url=source_url,  # Store source URL separately
                                            date_published=datetime.combine(date_published, datetime.min.time()),
                                            is_published=1 if is_published else 0
                                        )
                                        session.add(new_item)
                                        session.commit()
                                        st.success("Article extracted and saved successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error saving extracted article: {e}")
                                        session.rollback()
                        else:
                            st.error("Please enter a valid URL")
    
    # Display newsletter items
    st.subheader("Latest AI/ML News")
    
    # Get all published newsletter items, sorted by date (newest first)
    newsletter_items = session.query(Newsletter)
    
    # If not admin, only show published items
    if not st.session_state.get('is_admin'):
        newsletter_items = newsletter_items.filter(Newsletter.is_published == 1)
    
    newsletter_items = newsletter_items.order_by(Newsletter.date_published.desc()).all()
    
    if not newsletter_items:
        st.info("No newsletter items available yet. Check back later!")
        return
    
    for item in newsletter_items:
        with st.container():
            # Create a card-like container
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"### {item.title}")
                    st.caption(f"📅 {item.date_published.strftime('%B %d, %Y')}")
                    
                    # Display just the title as a summary (since we only kept the title as content)
                    st.markdown(f"🔹 {item.summary}")
                    
                    # Show source URL if available
                    if item.source_url:
                        st.markdown(f"[🔗 View Source]({item.source_url})", unsafe_allow_html=True)
                    elif item.image_url and item.image_url.startswith(('http://', 'https://')):
                        # For backward compatibility with existing items
                        st.markdown(f"[🔗 View Source]({item.image_url})", unsafe_allow_html=True)
                
                with col2:
                    # Show image if it exists and is a valid image URL
                    if item.image_url and not item.image_url.startswith(('http://', 'https://')):
                        st.image(item.image_url, use_container_width=True)
                    elif item.image_url and item.image_url != item.source_url:
                        st.image(item.image_url, use_container_width=True)
                
                # Admin actions - only show if user is admin
                if st.session_state.get('is_admin'):
                    with st.expander("Admin Actions", expanded=False):
                        st.caption(f"Status: {'✅ Published' if item.is_published else '📝 Draft'}")
                        
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button(f"✏️ Edit", key=f"edit_{item.id}"):
                                # Toggle edit mode for this item
                                st.session_state[f'editing_item_{item.id}'] = True
                                st.rerun()
                        
                        with col_del:
                            if st.button(f"🗑️ Delete", key=f"del_{item.id}"):
                                try:
                                    session.delete(item)
                                    session.commit()
                                    st.success("Item deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting item: {e}")
                                    session.rollback()
            
            # Add a subtle divider between items
            st.markdown("---", unsafe_allow_html=True)

def show_ai_culture():
    st.header("🤖 AI in Modern Culture")
    
    # Admin notice
    if st.session_state.get('is_admin'):
        st.success("🔧 Admin Mode: You can edit this content")
    
    # JARVIS section with image
    st.subheader("Decoding Iron Man's JARVIS")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        JARVIS (Just A Rather Very Intelligent System) is one of the most iconic AI systems in modern cinema.
        This section explores the real-world technologies that inspired JARVIS and how they're being implemented today.
        
        - **Voice Recognition**: Similar to today's Siri and Alexa
        - **Computer Vision**: Like in autonomous vehicles and security systems
        - **Natural Language Processing**: Used in chatbots and virtual assistants
        - **Home Automation**: Smart home integration we see with Google Home and Amazon Echo
        """)
    with col2:
        st.image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80", 
                caption="Iron Man's JARVIS - The AI Assistant", 
                use_container_width=True)
    
    st.markdown("---")
    # Add some interactive elements
    st.subheader("🚀 Real-world AI Applications")
    
    # Create tabs for different applications
    tab1, tab2, tab3 = st.tabs(["🏥 Healthcare", "💰 Finance", "🎬 Entertainment"])
    
    with tab1:
        st.header("AI in Healthcare")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("https://images.unsplash.com/photo-1576091160550-2173dba999ef?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80", 
                   caption="AI in Medical Diagnosis", 
                   use_container_width=True)
        with col2:
            st.write("""
            ### Transforming Healthcare with AI
            - **Medical Imaging Analysis**: AI algorithms can detect anomalies in X-rays, MRIs, and CT scans with high accuracy
            - **Drug Discovery**: Accelerating the process of finding new medications
            - **Personalized Treatment**: AI systems analyze patient data to recommend customized treatment plans
            - **Predictive Analytics**: Forecasting disease outbreaks and patient deterioration
            """)
        
        st.write("### Key Benefits")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**Faster Diagnosis**\n\nReducing diagnosis time from weeks to minutes")
        with col2:
            st.success("**Improved Accuracy**\n\nHigher accuracy in detecting diseases")
        with col3:
            st.warning("**Cost Reduction**\n\nLowering healthcare costs through automation")
    
    with tab2:
        st.header("AI in Finance")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("""
            ### Revolutionizing Financial Services
            - **Algorithmic Trading**: AI systems analyze market data and execute trades at optimal times
            - **Fraud Detection**: Real-time monitoring for suspicious activities
            - **Credit Scoring**: More accurate risk assessment using alternative data
            - **Personal Finance**: AI-powered financial advisors (robo-advisors)
            - **Regulatory Compliance**: Automating compliance and reporting
            """)
        with col2:
            st.image("https://images.unsplash.com/photo-1554224155-3a58922a22c3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80", 
                   caption="AI in Financial Markets", 
                   use_container_width=True)
        
        st.write("### Market Impact")
        st.metric("AI in Banking Market Size (2023)", "$64.03 Billion", "+32.6% YoY")
        st.progress(75)
        st.caption("Adoption rate of AI in financial services")
    
    with tab3:
        st.header("AI in Entertainment")
        st.image("https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80", 
               caption="AI in Content Creation", 
               use_container_width=True)
        
        st.write("### How AI is Changing Entertainment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Content Creation")
            st.write("""
            - **Deepfake Technology**: Creating realistic digital avatars
            - **AI-Generated Music**: Composing original scores
            - **Script Writing**: Assisting in story development
            - **Visual Effects**: Enhancing CGI in movies
            """)
            
        with col2:
            st.write("#### Personalization")
            st.write("""
            - **Recommendation Systems**: Netflix, Spotify, YouTube
            - **Interactive Content**: Choose-your-own-adventure stories
            - **Gaming**: Dynamic game environments and NPCs
            - **Virtual Influencers**: AI-generated social media personalities
            """)
        
        st.markdown("---")
        st.write("### Real-world Examples")
        st.success("🎬 **DeepMind's WaveNet** - Creating realistic synthetic voices for virtual assistants")
        st.info("🎵 **OpenAI's Jukebox** - Generating music in various styles and genres")
        st.warning("🎮 **AI Dungeon** - Text-based adventure game with AI-generated storylines")

def show_login():
    """Show login form and handle authentication"""
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        # Admin login
        if username == "admin" and password == "admin123":  # Change these credentials in production
            # Check if admin user exists, if not create it
            admin = session.query(User).filter_by(username="admin").first()
            if not admin:
                admin = User(username="admin", score=0, last_quiz_date=datetime.utcnow())
                session.add(admin)
                session.commit()
            
            st.session_state.user_id = admin.id
            st.session_state.is_admin = True
            st.session_state.username = "admin"
            st.sidebar.success("Logged in as Admin")
            st.rerun()
            
        elif username and password:  # Regular user
            # Check if user exists, if not create new user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                user = User(username=username, score=0, last_quiz_date=datetime.utcnow())
                session.add(user)
                session.commit()
            
            st.session_state.user_id = user.id
            st.session_state.is_admin = False
            st.session_state.username = username
            st.sidebar.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.sidebar.error("Please enter both username and password")
    
    if st.session_state.user_id:
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.session_state.is_admin = False
            st.rerun()

def main():
    st.set_page_config(
        page_title="AI/ML Learning Platform",
        page_icon="",
        layout="wide"
    )
    
    # Initialize show_quiz in session state if it doesn't exist
    if 'show_quiz' not in st.session_state:
        st.session_state.show_quiz = False
    
    st.sidebar.title("AI/ML Learning Platform")
    
    # Show login form if not logged in
    if not st.session_state.user_id:
        show_login()
        return
    
    # Navigation menu - show all options to all users
    user_menu = ["Home", "Quiz", "Leaderboard", "AI in Culture", "Newsletter"]
    
    # Add admin-only options
    if st.session_state.is_admin:
        user_menu.append("Create Quiz")
    
    # Show appropriate menu based on user role
    choice = st.sidebar.selectbox("Menu", user_menu)
    
    # If show_quiz is True, override the choice to show quiz
    if st.session_state.get('show_quiz', False):
        choice = "Quiz"
        st.session_state.show_quiz = False  # Reset the flag after using it
    
    # Show current user info
    st.sidebar.write("---")
    st.sidebar.write(f"{'Admin' if st.session_state.is_admin else 'User'} Mode")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.is_admin = False
        st.rerun()
    
    # Route to selected page
    if choice == "Home":
        show_home()
    elif choice == "Quiz":
        show_quiz()
    elif choice == "Leaderboard":
        show_leaderboard()
    elif choice == "Create Quiz" and st.session_state.is_admin:
        show_create_quiz()
    elif choice == "AI in Culture":
        show_ai_culture()
    elif choice == "Newsletter":
        show_newsletter()

if __name__ == "__main__":
    main()


