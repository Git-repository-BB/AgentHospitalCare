"""AgentCare Streamlit UI. Talks to the FastAPI backend over HTTP (JWT auth)."""
from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("AGENTCARE_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AgentCare", page_icon="🏥")
st.title("AgentCare")
st.caption("Non-clinical patient administration workflow, powered by LLM agents")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {st.session_state.token}"}


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
                st.session_state.token = data["access_token"]
                st.session_state.role = data["role"]
                st.session_state.username = username
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
                st.session_state.token = data["access_token"]
                st.session_state.role = data["role"]
                st.session_state.username = username
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Registration failed"))


def _workflow_ui() -> None:
    st.success(f"Signed in as {st.session_state.username} ({st.session_state.role})")
    if st.button("Log out"):
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

    with st.form("request_form"):
        patient_id = st.text_input("Patient ID")
        request_text = st.text_area(
            "Request", placeholder="Example: I need to register and book an appointment for cardiology"
        )
        submitted = st.form_submit_button("Submit")

    if submitted:
        resp = requests.post(
            f"{API_BASE_URL}/workflow",
            json={"request_text": request_text, "patient_id": patient_id or None},
            headers=_auth_headers(),
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
        resp = requests.get(f"{API_BASE_URL}/admin/escalations", headers=_auth_headers())
        if resp.ok:
            st.json(resp.json())

        st.write("### Admin: Audit log")
        resp = requests.get(f"{API_BASE_URL}/admin/audit-logs", headers=_auth_headers())
        if resp.ok:
            st.json(resp.json())


if not st.session_state.token:
    _login_register_ui()
else:
    _workflow_ui()
