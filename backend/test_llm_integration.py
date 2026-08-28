import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.llm import LLMClient, VisionClient, SessionManager, Prompts
from app.config import settings


def test_mock_llm_client():
    print("=" * 60)
    print("Test 1: LLMClient Mock Mode")
    print("=" * 60)
    client = LLMClient()
    print(f"Mock mode enabled: {client.mock_mode}")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "什么是意境？请简要解释。"},
    ]
    response = client.chat(messages)
    print(f"Response:\n{response}\n")
    assert "模拟回复" in response
    print("✓ LLMClient Mock mode works correctly!\n")


def test_mock_vision_client():
    print("=" * 60)
    print("Test 2: VisionClient Mock Mode")
    print("=" * 60)
    client = VisionClient()
    print(f"Mock mode enabled: {client.mock_mode}")
    response = client.analyze_image(
        prompt=Prompts.ART_VISUAL_OBSERVATION,
        image_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    )
    print(f"Response:\n{response}\n")
    assert "模拟视觉观察" in response
    print("✓ VisionClient Mock mode works correctly!\n")


def test_prompt_templates():
    print("=" * 60)
    print("Test 3: Prompt Templates")
    print("=" * 60)
    obs_prompt = Prompts.ART_VISUAL_OBSERVATION
    feedback_prompt = Prompts.format_art_teaching_feedback(
        observations="测试观察记录", context="学生的问题"
    )
    paper_prompt = Prompts.format_paper_analysis(content="测试论文内容")
    followup_prompt = Prompts.format_followup(
        history="历史对话", question="追问问题"
    )
    print(f"Art observation prompt length: {len(obs_prompt)} chars")
    print(f"Teaching feedback prompt length: {len(feedback_prompt)} chars")
    print(f"Paper analysis prompt length: {len(paper_prompt)} chars")
    print(f"Followup prompt length: {len(followup_prompt)} chars")
    assert "画面主体" in obs_prompt
    assert "值得肯定的探索" in feedback_prompt
    assert "核心观点提炼" in paper_prompt
    assert "对话历史" in followup_prompt
    print("✓ All prompt templates exist and are formatted correctly!\n")


def test_session_manager_isolation():
    print("=" * 60)
    print("Test 4: Session Manager - Isolation")
    print("=" * 60)
    manager = SessionManager()
    art_session = manager.create_session("art")
    paper_session = manager.create_session("paper")
    print(f"Art session ID: {art_session}")
    print(f"Paper session ID: {paper_session}")
    assert art_session.startswith("art_")
    assert paper_session.startswith("paper_")
    manager.add_message(art_session, "user", "这是艺术作品的问题")
    manager.add_message(art_session, "assistant", "这是艺术导师的回答")
    manager.add_message(paper_session, "user", "这是论文解读的问题")
    manager.add_message(paper_session, "assistant", "这是论文解读的回答")
    art_history = manager.get_history(art_session)
    paper_history = manager.get_history(paper_session)
    print(f"Art session messages: {len(art_history)}")
    print(f"Paper session messages: {len(paper_history)}")
    assert len(art_history) == 2
    assert len(paper_history) == 2
    assert "艺术作品" in art_history[0]["content"]
    assert "论文解读" in paper_history[0]["content"]
    assert "艺术作品" not in paper_history[0]["content"]
    assert "论文解读" not in art_history[0]["content"]
    art_info = manager.get_session_info(art_session)
    paper_info = manager.get_session_info(paper_session)
    print(f"Art session type: {art_info['agent_type']}")
    print(f"Paper session type: {paper_info['agent_type']}")
    assert art_info["agent_type"] == "art"
    assert paper_info["agent_type"] == "paper"
    print("✓ Session isolation works correctly! Messages do not interfere between sessions.\n")


def test_session_manager_clear():
    print("=" * 60)
    print("Test 5: Session Manager - Clear Session")
    print("=" * 60)
    manager = SessionManager()
    session = manager.create_session("art")
    manager.add_message(session, "user", "测试消息")
    assert manager.session_exists(session)
    result = manager.clear_session(session)
    assert result is True
    assert not manager.session_exists(session)
    history = manager.get_history(session)
    assert len(history) == 0
    print("✓ Session clearing works correctly!\n")


def test_config_loading():
    print("=" * 60)
    print("Test 6: Configuration Loading")
    print("=" * 60)
    print(f"App name: {settings.app_name}")
    print(f"LLM API base: {settings.llm_api_base}")
    print(f"LLM model: {settings.llm_model}")
    print(f"LLM API key set: {bool(settings.llm_api_key)}")
    print(f"Vision API base: {settings.vision_api_base}")
    print(f"Vision model: {settings.vision_model}")
    print(f"Vision API key set: {bool(settings.vision_api_key)}")
    assert settings.llm_api_base
    assert settings.llm_model
    assert settings.vision_api_base
    assert settings.vision_model
    print("✓ Configuration loaded correctly!\n")


def test_session_id_validation():
    print("=" * 60)
    print("Test 7: Session ID Validation")
    print("=" * 60)
    manager = SessionManager()
    try:
        manager.add_message("invalid_session", "user", "test")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Correctly rejected invalid session ID: {e}")
    print("✓ Session ID validation works correctly!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LLM Integration Layer Test Suite")
    print("=" * 60 + "\n")
    try:
        test_config_loading()
        test_mock_llm_client()
        test_mock_vision_client()
        test_prompt_templates()
        test_session_manager_isolation()
        test_session_manager_clear()
        test_session_id_validation()
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
