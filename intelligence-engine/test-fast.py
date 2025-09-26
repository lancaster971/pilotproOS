#!/usr/bin/env python3
"""
Fast test script for Intelligence Engine
Tests basic functionality without full stack
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import streamlit as st

# Test FastAPI
app = FastAPI(title="Intelligence Engine Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Intelligence Engine Test Running", "langchain": "ready"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting Fast Test Server...")
    print("API: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)