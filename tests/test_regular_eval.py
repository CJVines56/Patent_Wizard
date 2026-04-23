from types import SimpleNamespace

from backend.orchestrator import regular_eval as reval


def test_extract_cleaned_question_prefers_cleaned_query():
    final_state = {"cleaned_query": "cleaned question"}

    assert reval.extract_cleaned_question(final_state, "fallback") == "cleaned question"


def test_extract_cleaned_question_falls_back_to_last_user_message():
    final_state = {
        "messages": [
            {"role": "user", "content": "original question"},
            {"role": "assistant", "content": "answer"},
            SimpleNamespace(type="human", content="cleaned question"),
        ]
    }

    assert reval.extract_cleaned_question(final_state, "fallback") == "cleaned question"


def test_resolve_questions_path_falls_back_to_existing_i_file(tmp_path, monkeypatch):
    repo_root = tmp_path
    validation_dir = repo_root / "backend" / "orchestrator"
    validation_dir.mkdir(parents=True)
    existing = validation_dir / "regular_validation_I.txt"
    existing.write_text("Question\nExample\n", encoding="utf-8")

    monkeypatch.setattr(reval, "_repo_root", lambda: repo_root)

    assert reval.resolve_questions_path() == existing


def test_build_eval_rows_uses_distinct_thread_ids(monkeypatch):
    thread_ids = []

    def fake_run(app, question, thread_id, app_rpm_budget):
        thread_ids.append(thread_id)
        return {
            "user_input": question,
            "response": "answer",
            "retrieved_contexts": ["context"],
        }

    monkeypatch.setattr(reval, "run_one_with_graph", fake_run)

    rows = reval.build_eval_rows(object(), ["q1", "q2"], thread_prefix="session", app_rpm_budget=12)

    assert len(rows) == 2
    assert thread_ids == ["session-1", "session-2"]
