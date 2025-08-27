import pytest
from unittest.mock import patch, MagicMock
from quiz_manager import (
    get_random_question,
    update_player_progress,
    init_player_progress,
    player_progress,
    user_question_pools,
    ALL_QUIZZES
)

class TestQuizManager:
    """Test suite for QuizManager functionality"""
    
    def setup_method(self):
        """Reset state before each test"""
        player_progress.clear()
        user_question_pools.clear()
    
    def test_init_player_progress(self):
        """Test initializing player progress"""
        user_id = 12345
        init_player_progress(user_id)
        
        assert user_id in player_progress
        progress = player_progress[user_id]
        assert progress['current_streak'] == 0
        assert progress['best_streak'] == 0
        assert progress['total_correct'] == 0
        assert progress['total_questions'] == 0
        assert progress['questions_until_bonus'] == 10
        assert progress['skips_used'] == 0
        assert progress['games_paused'] == 0
    
    def test_update_player_progress_correct(self):
        """Test updating progress for correct answer"""
        user_id = 12345
        init_player_progress(user_id)
        
        # First correct answer
        bonus_earned = update_player_progress(user_id, True)
        progress = player_progress[user_id]
        
        assert progress['current_streak'] == 1
        assert progress['best_streak'] == 1
        assert progress['total_correct'] == 1
        assert progress['total_questions'] == 1
        assert progress['questions_until_bonus'] == 9
        assert not bonus_earned
    
    def test_update_player_progress_incorrect(self):
        """Test updating progress for incorrect answer"""
        user_id = 12345
        init_player_progress(user_id)
        
        # First set up some progress
        update_player_progress(user_id, True)
        update_player_progress(user_id, True)
        
        # Then incorrect answer
        bonus_earned = update_player_progress(user_id, False)
        progress = player_progress[user_id]
        
        assert progress['current_streak'] == 0
        assert progress['best_streak'] == 2
        assert progress['total_correct'] == 2
        assert progress['total_questions'] == 3
        assert progress['questions_until_bonus'] == 10
        assert not bonus_earned
    
    def test_update_player_progress_bonus(self):
        """Test bonus earning after 10 correct answers"""
        user_id = 12345
        init_player_progress(user_id)
        
        # Answer 10 questions correctly
        bonus_earned = False
        for i in range(10):
            bonus_earned = update_player_progress(user_id, True)
        
        progress = player_progress[user_id]
        
        assert bonus_earned
        assert progress['current_streak'] == 0  # Reset after bonus
        # The best_streak should be 9 because it's set before the bonus reset
        assert progress['best_streak'] == 9
        assert progress['total_correct'] == 10
        assert progress['total_questions'] == 10
        assert progress['questions_until_bonus'] == 10  # Reset to 10
    
    def test_get_random_question_first_time(self):
        """Test getting a random question for new user"""
        user_id = 12345
        
        question = get_random_question(user_id)
        
        assert question is not None
        assert 'q' in question
        assert 'a' in question
        assert 'choices' in question
        assert len(question['choices']) == 4
        assert user_id in user_question_pools
        assert len(user_question_pools[user_id]) == 1
    
    def test_get_random_question_unique_questions(self):
        """Test that questions are unique until pool is exhausted"""
        user_id = 12345
        
        # Get all questions to ensure we test the reset logic
        total_questions = len(ALL_QUIZZES)
        questions_received = []
        
        for i in range(total_questions + 5):  # Get more than available to test reset
            question = get_random_question(user_id)
            questions_received.append(question['q'])
        
        # Should have received all questions at least once
        unique_questions = set(questions_received)
        assert len(unique_questions) == total_questions
        
        # The pool should have been reset and we should start getting repeats
        assert len(questions_received) > total_questions
    
    def test_quiz_data_integrity(self):
        """Test that all quiz data has proper structure"""
        for quiz in ALL_QUIZZES:
            assert 'q' in quiz, f"Quiz missing question: {quiz}"
            assert 'a' in quiz, f"Quiz missing answer: {quiz}"
            assert 'choices' in quiz, f"Quiz missing choices: {quiz}"
            assert len(quiz['choices']) == 4, f"Quiz should have 4 choices: {quiz}"
            assert quiz['a'] in quiz['choices'], f"Answer not in choices: {quiz}"
    
    def test_african_countries_data(self):
        """Test African countries data structure"""
        from quiz_manager import AFRICAN_COUNTRIES
        
        assert len(AFRICAN_COUNTRIES) > 0
        for country in AFRICAN_COUNTRIES:
            assert 'name' in country
            assert 'website' in country
            assert 'bio' in country
            assert isinstance(country['name'], str)
            assert isinstance(country['website'], str)
            assert isinstance(country['bio'], str)

def test_quiz_content_quality():
    """Test that quiz questions are meaningful and well-formed"""
    for quiz in ALL_QUIZZES:
        # Check question length
        assert len(quiz['q']) > 10, f"Question too short: {quiz['q']}"
        assert len(quiz['q']) < 200, f"Question too long: {quiz['q']}"
        
        # Check answer length
        assert len(quiz['a']) > 1, f"Answer too short: {quiz['a']}"
        assert len(quiz['a']) < 100, f"Answer too long: {quiz['a']}"
        
        # Check choices are unique
        choices = quiz['choices']
        assert len(choices) == len(set(choices)), f"Duplicate choices found: {choices}"
        
        # Check choices are reasonable length
        for choice in choices:
            assert len(choice) > 0, f"Empty choice found: {choice}"
            assert len(choice) < 50, f"Choice too long: {choice}"
