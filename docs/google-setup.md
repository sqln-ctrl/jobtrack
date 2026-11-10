# Google Cloud setup

1. Create a project at console.cloud.google.com and enable the **Gmail API**.
2. OAuth consent screen: External, add yourself under **Test users** (testing mode allows up to 100 users and needs no verification).
3. Add scopes: `openid`, `email`, `profile` and `https://www.googleapis.com/auth/gmail.readonly`.
4. Credentials, OAuth client ID, Web application. Authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/google/callback`
   - `http://localhost:8000/api/v1/gmail/callback`
5. Copy the client ID and secret into `backend/.env`.

`gmail.readonly` is a **restricted scope**. Before a public launch you need Google's OAuth verification and a security assessment (CASA). Plan for this early.
