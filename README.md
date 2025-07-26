# AI/ML World

An interactive Streamlit application that explores the world of Artificial Intelligence and Machine Learning through quizzes, news, and educational content.

## Features

### Quiz System
- Interactive AI/ML quizzes with score tracking
- Multiple-choice questions with instant feedback
- Progress tracking and final score display
- Quiz review with correct answers

### AI in Culture
- Explore AI applications in various domains
- Interactive tabs for different industries (Healthcare, Finance, Entertainment)
- Rich media content and visualizations

### Newsletter
- Daily AI/ML news updates
- Article extraction from URLs
- Admin panel for content management
- Responsive design for all devices

### User System
- Simple login system
- Admin and regular user roles
- Score leaderboard

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-ml-world.git
cd ai-ml-world
```

2. Create and activate a virtual environment (recommended):
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run streamlit_app.py
```

5. Open your browser and navigate to `http://localhost:8501`

## 📂 Project Structure

```
.
├── streamlit_app.py      # Main application file
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## 🔧 Technologies Used

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite (via SQLAlchemy)
- **Key Libraries**:
  - Pandas & NumPy (Data Processing)
  - Plotly (Visualizations)
  - Newspaper3k (Article Extraction)
  - BeautifulSoup & Requests (Web Scraping)
  - PyPDF2 & pdfplumber (PDF Processing)

## 👥 User Guide

### Default Login Credentials
- **Admin**:
  - Username: `admin`
  - Password: `admin123`
- **Regular User**: Any username/password combination (auto-registration)

### Adding Quiz Questions
1. Log in as admin
2. Go to "Create Quiz"
3. Add questions manually or import from PDF
4. Set correct answers and save

### Managing Newsletter
1. Log in as admin
2. Go to "Newsletter"
3. Add new items manually or extract from URL
4. Publish to make them visible to users

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Streamlit for the amazing framework
- All open-source libraries used in this project
- The AI/ML community for continuous inspiration
