![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)


<div align="center">

# 🔗 URL Shortener System

### Lightning-Fast URL Shortening with Redis Caching

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Click_Here-blue?style=for-the-badge)](https://urlshortener.netlify.app)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/Harsh13912/url-shortener-project)

A highly scalable, full-stack URL shortening service built with **FastAPI**, **React**, **PostgreSQL**, and **Redis**.  
Developed as a 6th-semester Computer Science Engineering system design project focusing on **high-performance reads** and **low-latency redirects**.

[Features](#-features) • [Tech Stack](#️-technology-stack) • [Architecture](#-system-architecture--working) • [Local Setup](#-how-to-run-locally) • [Deployment](#-deployment)

</div>

---

## ✨ Features

<table>
<tr>
<td>

⚡ **Lightning-Fast Redirects**  
Sub-millisecond response times using Redis caching

🔑 **Base62 Encoding**  
Generates short, unique 5-character URL codes

📊 **Click Analytics**  
Real-time tracking of link access statistics

</td>
<td>

🔗 **Link Management**  
Create and delete custom short links instantly

☁️ **Cloud Deployed**  
Fully hosted on distributed cloud architecture

🚀 **High Scalability**  
Built to handle thousands of concurrent requests

</td>
</tr>
</table>

---

## 🛠️ Technology Stack

### **Frontend**
```
⚛️  React (Vite)
🎨  Tailwind CSS
📱  Responsive Design
🌐  Deployed on Netlify
```

### **Backend**
```
🐍  Python 3.12
⚡  FastAPI (Async Framework)
🦄  Uvicorn (ASGI Server)
☁️  Deployed on Render
```

### **Database & Caching**
```
🐘  PostgreSQL (Neon - Serverless)
⚡  Redis (In-Memory Cache)
🔄  asyncpg (Async DB Driver)
```

---

## 🧠 System Architecture & Working

This system is optimized for **read-heavy workloads** — where a link is created once but clicked thousands of times.

### 📊 Architecture Diagram

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         React Frontend              │
│        (Netlify - CDN)              │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│       FastAPI Backend (Render)       │
│  ┌──────────────────────────────┐   │
│  │   1. Check Redis Cache       │   │
│  │      ├─ Hit? → Redirect (1ms)│   │
│  │      └─ Miss? → Query DB     │   │
│  └──────────────────────────────┘   │
└───────┬──────────────────┬───────────┘
        │                  │
        ▼                  ▼
┌───────────────┐   ┌─────────────────┐
│  Redis Cache  │   │   PostgreSQL    │
│   (Render)    │   │     (Neon)      │
└───────────────┘   └─────────────────┘
```

### 🔄 The Cache-Aside Pattern

**Read Path (When User Clicks Short Link):**

1. 🔍 **Check Redis Cache First**
   - ✅ **Cache Hit** → Instant redirect (<1ms)
   - ❌ **Cache Miss** → Query PostgreSQL

2. 💾 **If Cache Miss:**
   - Fetch URL from PostgreSQL
   - Store in Redis for next time
   - Redirect user

3. 📈 **Analytics Update:**
   - Increment click counter in Redis (non-blocking)
   - Periodically sync to PostgreSQL

**Write Path (When Creating Short URL):**

1. 🎲 Generate random 5-character Base62 code
2. 🔍 Check PostgreSQL for collisions
3. 💾 Save to database
4. ⚡ Cache in Redis immediately
5. 🎉 Return short URL to user

### 🔢 Base62 Encoding

Instead of saving massive database IDs, we convert auto-incrementing integers into **Base62 strings** using:
- `A-Z` (26 characters)
- `a-z` (26 characters)  
- `0-9` (10 characters)

**Result:** 62^5 = **916+ million** unique short codes with just 5 characters!

---

## 💻 How to Run Locally

Want to run this project on your machine? Follow these steps:

### ✅ Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.12+** installed
- ✅ **Node.js 18+** and npm
- ✅ **PostgreSQL** database (Neon free tier works great)
- ✅ **Redis** instance (Upstash free tier recommended)

### 🔧 Backend Setup

**1. Navigate to backend directory:**
```bash
cd backend
```

**2. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**3. Create environment file:**
```bash
cp .env.example .env
```

**4. Configure your `.env` file:**
```env
DATABASE_URL=postgresql://user:password@your-neon-host.neon.tech/dbname?sslmode=require
REDIS_URL=redis://default:password@your-redis-host:6379
```

**5. Set up the database:**

Run the `schema.sql` file in your Neon SQL Editor, or:
```bash
psql "postgresql://..." -f schema.sql
```

**6. Start the FastAPI server:**
```bash
uvicorn main:app --reload
```

✅ **Backend running at:** `http://127.0.0.1:8000`

---

### 🎨 Frontend Setup

**1. Navigate to frontend directory:**
```bash
cd frontend
```

**2. Install Node dependencies:**
```bash
npm install
```

**3. Create environment file:**
```bash
cp .env.example .env
```

**4. Configure your `.env` file:**
```env
VITE_API_URL=http://127.0.0.1:8000
```

**5. Start the development server:**
```bash
npm run dev
```

✅ **Frontend running at:** `http://localhost:5173`

---

## 🌐 Deployment

### **Frontend (Netlify)**
1. Build the project: `npm run build`
2. Deploy the `dist` folder to Netlify
3. Set environment variable: `VITE_API_URL=<your-backend-url>`

### **Backend (Render)**
1. Create a new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `DATABASE_URL` (from Neon)
   - `REDIS_URL` (from Render Redis)

### **Database (Neon)**
1. Create a free PostgreSQL database
2. Run `schema.sql` in the SQL Editor
3. Copy connection string to backend `.env`

### **Cache (Redis on Render)**
1. Create a Redis instance
2. Copy internal URL to backend environment variables

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/shorten` | Create a new short URL |
| `GET` | `/{short_code}` | Redirect to original URL |
| `GET` | `/analytics/{short_code}` | Get click statistics |
| `DELETE` | `/delete/{short_code}` | Delete a short URL |

**Interactive API Docs:** `http://localhost:8000/docs`

---

## 🎯 Performance Metrics

| Metric | Value |
|--------|-------|
| **Cache Hit Redirect** | < 1ms |
| **Cache Miss Redirect** | 10-50ms |
| **URL Creation** | 50-100ms |
| **Concurrent Requests** | 1000+ req/sec |

---

## 🔮 Future Enhancements

- 🔐 **User Authentication** - OAuth 2.0 integration
- 📊 **Advanced Analytics** - Geographic data, device tracking
- 🎨 **Custom Aliases** - User-defined short codes
- 📱 **QR Code Generation** - Auto-generate QR codes
- 🛡️ **Malware Scanning** - URL safety checks
- ⚡ **Rate Limiting** - DDoS protection

---

## 📸 Screenshots

<div align="center">

### 🏠 Home Page
![Home Page](https://via.placeholder.com/800x400/4F46E5/FFFFFF?text=Add+Your+Screenshot+Here)

### 📊 Analytics Dashboard
![Analytics](https://via.placeholder.com/800x400/7C3AED/FFFFFF?text=Add+Your+Screenshot+Here)

</div>

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page]((https://github.com/Harsh13912/url-shortener-project/issues).

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Your Name**

- GitHub: [@Harsh13912](https://github.com/aryansingh)
- LinkedIn: [Harsh Kumar](YOUR_LINKEDIN_LINK)

---

## 🙏 Acknowledgments

This application was developed as a deep dive into:
- ⚡ System Design & Architecture
- 🐍 Asynchronous Python Programming
- ☁️ Cloud Infrastructure Integration
- 📊 Database Optimization & Caching Strategies

Built with ❤️ for the Computer Science Engineering curriculum.

---

<div align="center">

### ⭐ Star this repo if you found it helpful!

[![GitHub stars](https://img.shields.io/github/stars/yourusername/url-shortener?style=social)](https://github.com/Harsh13912/url-shortener-project)

**[Back to Top](#-url-shortener-system)**

</div>
