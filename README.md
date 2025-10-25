## SECTION 1 : PROJECT TITLE
## Singapore Housing & Deveoplment Board - BTO Recommender System


---

## SECTION 2 : EXECUTIVE SUMMARY / PAPER ABSTRACT
Singapore's dense population creates a high demand for rental housing, particularly among young professionals, expatriates, and students. As Singapore’s total population reached a record 6.11 million in mid-2025, driven primarily by growth in foreign workers , this influx of renters increases pressure on the housing supply. However, tenants face a challenging search process, as rental information is fragmented across multiple online platforms like PropertyGuru and 99.co. These existing platforms primarily offer basic, rigid filtering capabilities (e.g., price ranges, property size) and fail to capture tenants’ personalized preferences and lifestyle considerations—such as a willingness to pay more for better lighting, quieter environments, or proximity to transport.

Our team recognized this gap between high market demand and low decision-making efficiency and aimed to bridge this knowledge gap by creating an intelligent rental recommendation system. Our project utilizes Singapore property listing data sourced from the public Inside Airbnb repository to provide personalized, context-aware suggestions , aiming to improve tenants' search efficiency and overall rental satisfaction.

Using the techniques imparted to us in our courses, our group first set out to build a sizeable knowledge base by conducting extensive data cleaning and preprocessing on the raw Airbnb data. The system utilizes a Content-Based Recommendation algorithm , building a cosine similarity matrix to measure the similarity between listings. Furthermore, the system incorporates a weighted scoring mechanism based on user interactions (like "likes" and "views") to enhance personalization. For our tech stack, we utilized Next.js for the frontend , Python Flask for the backend , and a MySQL database. To add icing on the cake, we even integrated an LLM Chatbot using LangChain and Gemini-2.5 , which can assist users by answering natural language queries about travel time or nearby amenities. The entire system was containerized using Docker for easy deployment.

Our team had a meaningful and enjoyable experience building this system, allowing us to practice our full-stack development skills while learning to implement a recommendation algorithm and integrate an agentic language model. We hope to share our insights on improving the rental search process. This project demonstrates the application of intelligent reasoning to a real-world system , and we only wish there was more time to work on future improvements, such as incorporating real-time data updates and adding user-based collaborative filtering methods.


## SECTION 3 : USER GUIDE

- Download Singapore `listings.csv` from https://insideairbnb.com/get-the-data .
- Run `recommendation-service/data/Consine_Similarity_Calculation.ipynb` in notebook.
- Place the result `cosine_similarity.csv` into `recommendation-service/data`.
- Install `docker` and `docker-compose`.
- Run `docker compose up --build` in current directory, and wait a few seconds for backend and database containers.
- Open `http://localhost:3000` in web browser. 

---
## SECTION 4 : PROJECT REPORT / PAPER

`Refer to project report at Github Folder: ProjectReport`

**Recommended Sections for Project Report / Paper:**
1. Project Background
2. Problem Description
3. Project Solution
4. System Implementation
5. Future Improvement
6. Appendix A – Project Proposal
7. Appendix B – Mapping of System Functionalities to Courses
8. Appendix C – User Guide
9. Appendix D – Individual Member Report

---