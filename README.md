# Smart-Voting-App
A secure online voting system using face recognition built with Python, Flask, OpenCV, and MySQL. It allows users to vote after facial verification, ensuring one person can vote only once. Admins can manage candidates, train the model, and view results.

📦 Modules
1. User Registration Module
This module allows new users to register by uploading frontal face images. A unique Voter ID is generated and stored along with user details in the database. The face data is later used for recognition during the voting process.

2. Face Detection and Recognition Module
Uses OpenCV’s Haar Cascade for face detection and LBPH for face recognition. During login, the system captures live video, detects the face, and matches it with the trained model to verify the voter’s identity.

3. Voting Module
After successful facial recognition, users are shown the list of candidates. They can cast one vote, which is securely recorded in the database to ensure no duplicate votes.

4. Admin Module
Admins can log in to manage the election process. They can add candidates, view registered users, train the recognition model with new faces, and monitor voting results in real time.

5. Model Training Module
This module collects the uploaded facial images and uses them to train the recognition model using OpenCV. It ensures the system is up-to-date with all registered users for accurate face matching.

6. Database Module
All user information, facial data paths, voting logs, and admin configurations are stored in a MySQL database. This ensures data integrity, security, and smooth system operations.
