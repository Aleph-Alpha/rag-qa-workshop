# Setup

1. Get Aleph Alpha API Token.
    1. Goto your personal [profile page](https://app.aleph-alpha.com/profile).
    2. Click on "Create Token".
    3. Save the generated token.
2. Install and start Trace Viewer
    1. Artifactory Token
        1. Goto [Artifactory](https://alephalpha.jfrog.io/ui/login/) and use the "Forgot Password?" function to set a password.
        2. Log in. 
        3. Click on your profile icon in the top-right corner and click on "Set Me Up".
        4. Click on "Generic".
        5. Enter your password and click on "Generate Token & Create Instructions".
        6. Save the generated token.
    2. Run `docker login https://alephalpha.jfrog.io --username YOUR_EMAIL --password YOUR_TOKEN` (Fill in your email and token!)
    3. Run `docker run -p 3000:3000 alephalpha.jfrog.io/container-images/trace-viewer:latest`
3. Setup python environment
    1. Run `poetry install`
5. Start streamlit app
    1. Run `poetry run streamlit run ./day_1/app.py`
