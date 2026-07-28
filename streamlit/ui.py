"""AgentCare Streamlit UI. Talks to the FastAPI backend over HTTP (Basic Auth)."""
from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("AGENTCARE_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AgentCare", page_icon="🏥")
st.title("AgentCare")
st.caption("Non-clinical patient administration workflow, powered by LLM agents")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.password = None


def _auth() -> tuple[str, str]:
    return (st.session_state.username, st.session_state.password)


def _login_register_ui() -> None:
    st.subheader("Sign in")
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
        if submitted:
            resp = requests.post(f"{API_BASE_URL}/auth/login", json={"username": username, "password": password})
            if resp.ok:
                data = resp.json()
                st.session_state.authenticated = True
                st.session_state.role = data["role"]
                st.session_state.username = username
                st.session_state.password = password
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Login failed"))

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("Username", key="register_username")
            password = st.text_input("Password", type="password", key="register_password")
            submitted = st.form_submit_button("Register as patient")
        if submitted:
            resp = requests.post(f"{API_BASE_URL}/auth/register", json={"username": username, "password": password})
            if resp.ok:
                data = resp.json()
                st.session_state.authenticated = True
                st.session_state.role = data["role"]
                st.session_state.username = username
                st.session_state.password = password
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Registration failed"))


def _workflow_ui() -> None:
    st.success(f"Signed in as {st.session_state.username} ({st.session_state.role})")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.password = None
        st.rerun()

    with st.form("request_form"):
        patient_id = st.text_input("Patient ID")
        request_text = st.text_area(
            "Request", placeholder="Example: I need to register and book an appointment for cardiology"
        )
        uploaded_files = st.file_uploader("Documents", accept_multiple_files=True)
        submitted = st.form_submit_button("Submit")

    if submitted:
        if uploaded_files:
            files = [
                ("files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))
                for uploaded_file in uploaded_files
            ]
            resp = requests.post(
                f"{API_BASE_URL}/workflow/upload",
                data={"request_text": request_text, "patient_id": patient_id},
                files=files,
                auth=_auth(),
            )
        else:
            resp = requests.post(
                f"{API_BASE_URL}/workflow",
                json={"request_text": request_text, "patient_id": patient_id or None},
                auth=_auth(),
            )
        if resp.ok:
            result = resp.json()
            st.success(result["summary"])
            st.write("### Workflow result")
            st.json(result)
        else:
            st.error(resp.json().get("detail", "Request failed"))

    if st.session_state.role == "administrator":
        st.write("---")
        st.write("### Admin: Escalations")
        resp = requests.get(f"{API_BASE_URL}/admin/escalations", auth=_auth())
        if resp.ok:
            st.json(resp.json())

        st.write("### Admin: Audit log")
        resp = requests.get(f"{API_BASE_URL}/admin/audit-logs", auth=_auth())
        if resp.ok:
            st.json(resp.json())


if not st.session_state.authenticated:
    _login_register_ui()
else:
    _workflow_ui()
