<div align="center">

# 🎯 MIMO PREDICTIVE SNIPER

**Fully Autonomous On-Chain Prediction Market Agent Powered by Xiaomi Mimo AI**

[![Powered By Mimo](https://img.shields.io/badge/Powered_By-Xiaomi_Mimo_AI-FF6900?style=for-the-badge&logo=xiaomi&logoColor=white)](https://platform.xiaomimimo.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Polygon Network](https://img.shields.io/badge/Network-Polygon-8247E5?style=for-the-badge&logo=polygon&logoColor=white)](https://polygon.technology/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](#)

[Features](#-key-features) • [Architecture](#-system-architecture) • [Installation](#-quick-start) • [Configuration](#-environment-variables) • [Disclaimer](#-disclaimer)

</div>

---

## 💡 Overview

**MIMO PREDICTIVE SNIPER** is a pure, low-latency CLI daemon designed to hunt for mispriced events on Polymarket (or any Conditional Tokens Framework based prediction market). 

By leveraging the advanced reasoning capabilities of the **Xiaomi Mimo AI Platform**, this agent processes real-time political, crypto, and global news streams, calculates the probability of future events, and autonomously executes Web3 transactions when the AI's confidence significantly outweighs current market odds.

This project was built to demonstrate the superior **NLP comprehension and low-latency inference** of the Xiaomi Mimo AI ecosystem in high-stakes, time-critical financial environments.

---

## 🔥 Key Features

- **🧠 Mimo-Powered Probability Router:** Utilizes `mimo-v1` for complex sentiment and factual analysis, acting as the core "Brain" for event probability scoring.
- **⚡ Smart Fallback Mechanism:** Built-in multi-tier AI routing ensures 100% uptime. If the primary engine experiences high loads, it seamlessly falls back to secondary models.
- **📡 Real-Time Ingestion:** Continuous background streaming of global RSS feeds (Reuters, CoinDesk, etc.) with automated deduplication.
- **⚖️ Dynamic Market Evaluator:** Mathematical edge-calculation logic `(AI_Probability - Market_Price >= Minimum_Margin)`.
- **🔗 Native Web3 Execution:** Zero human-in-the-loop. Automatically signs and broadcasts USDC transactions directly to the Polygon RPC using `web3.py`.

---

## 🏗 System Architecture

The daemon operates in a continuous, asynchronous loop consisting of 4 immutable core modules:

```mermaid
graph TD;
    A[Global News/RSS Feeds] -->|Stream| B(MIMO_INGESTION);
    B -->|Raw Text Data| C{MIMO_PROBABILITY_ROUTER};
    C -->|API Request| D((Xiaomi Mimo AI Platform));
    D -->|0.0 - 1.0 Probability| C;
    C -->|Probability Score| E(MARKET_EVALUATOR);
    E -->|Check Edge > 20%| F{Is Mispriced?};
    F -->|Yes| G[WEB3_EXECUTION];
    F -->|No| H[Skip / Continue Loop];
    G -->|Sign Tx| I[(Polygon Network)];