"""Carregamento de dados e estado operacional do dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from simulation.event_buffer import BufferedEvent, EventBuffer
from simulation.traffic_stream import TrafficStream

from models.predict import ModelPredictor, load_test_data
from utils.config import load_config
from utils.io import load_json
from utils.paths import MODELS_DIR


@st.cache_resource
def get_predictor() -> ModelPredictor:
    return ModelPredictor()


@st.cache_data
def get_test_predictions() -> pd.DataFrame:
    predictor = get_predictor()
    test_df = load_test_data()
    return predictor.predict_batch(test_df)


@st.cache_data
def get_training_summary() -> dict:
    path = MODELS_DIR / "training_summary.json"
    if path.exists():
        return load_json(path)
    return {}


def init_operational_state() -> None:
    config = load_config()
    sim = config["simulation"]
    if "stream" not in st.session_state:
        st.session_state.stream = TrafficStream(get_predictor())
    if "event_buffer" not in st.session_state:
        st.session_state.event_buffer = EventBuffer(
            capacity=sim["buffer_size"]
        )
        bootstrap = sim["bootstrap_on_start"]
        for _ in range(bootstrap):
            push_next_event()


def push_next_event() -> BufferedEvent:
    event = st.session_state.stream.next_event()
    buffered = BufferedEvent.from_traffic_event(event, event.row)
    st.session_state.event_buffer.push(buffered)
    return buffered


def tick_stream(n: int | None = None) -> None:
    config = load_config()
    count = n if n is not None else config["simulation"]["tick_per_refresh"]
    for _ in range(count):
        push_next_event()


def operational_dataframe() -> pd.DataFrame:
    return st.session_state.event_buffer.to_dataframe()
