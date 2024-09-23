import telebot
from telebot import types
import json
import os

# Создаем экземпляр бота
TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'messages.json'  # Укажите полный путь к файлу, если необходимо

# Create dictionaries to store user states and temporary data
user_states = {}
user_data = {}

# Define the list of positions
POSITIONS = [
    'Product Manager',
    'Tracker/Project Manager',
    'Content Creator',
    'Marketer',
    'Frontend Developer',
    'Backend Developer',
    'DevOps Engineer',
    'Psychologist',
    'Designer',
    'Data Scientist',
    'Fundraising Manager'
]

# Function to get the main keyboard
# Функция для получения основной клавиатуры
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_write = types.KeyboardButton('Write a review')
    button_read = types.KeyboardButton('Read reviews')
    markup.add(button_write, button_read)
    return markup

# Функция для создания клавиатуры с цифрами от 1 до 5 в одном ряду
def get_rating_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(str(i)) for i in range(1, 6)]
    markup.row(*buttons)  # Располагаем все кнопки в одном ряду
    return markup

# Функция инициализации файла данных
def init_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f)
        print("Data file created.")

# Функция загрузки сообщений из файла
def load_messages():
    if not os.path.exists(DATA_FILE):
        init_data_file()  # Создаем файл, если он не существует
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                # Файл пустой, инициализируем пустым словарем
                data = {}
                save_messages(data)
            else:
                data = json.loads(content)
            return data
    except json.JSONDecodeError as e:
        print(f"JSON loading error: {e}")
        # Переинициализируем файл пустым словарем
        data = {}
        save_messages(data)
        return data

# Функция сохранения сообщений в файл
def save_messages(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"I/O error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_bot(message):
    first_msg = f"Hello {message.from_user.first_name} {message.from_user.last_name}!\nThis is an employee review bot. Please choose an option:"
    markup = get_main_keyboard()
    bot.send_message(message.chat.id, first_msg, reply_markup=markup)

# Handle main menu buttons
@bot.message_handler(func=lambda message: message.text in ['Write a review', 'Read reviews'])
def handle_buttons(message):
    global user_states, user_data
    user_id = message.from_user.id

    # Reset user state and data
    user_states[user_id] = None
    user_data[user_id] = {}

    if message.text == 'Write a review':
        # Start the review process
        user_data[user_id]['review'] = {}
        user_states[user_id] = 'awaiting_position_selection'
        send_positions_keyboard(message.chat.id, user_id)
    elif message.text == 'Read reviews':
        # Offer new options
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_view_reviews = types.KeyboardButton('View reviews')
        button_view_summary = types.KeyboardButton('View overall summary')
        back_button = types.KeyboardButton('Back to main menu')
        markup.add(button_view_reviews, button_view_summary)
        markup.add(back_button)
        bot.send_message(message.chat.id, "Please choose an option:", reply_markup=markup)

# Handle options after 'Read reviews'
@bot.message_handler(func=lambda message: message.text in ['View reviews', 'View overall summary'])
def handle_read_reviews_options(message):
    if message.text == 'View reviews':
        show_reviews(message.chat.id)
    elif message.text == 'View overall summary':
        show_overall_summary(message.chat.id)

# Function to send positions keyboard
def send_positions_keyboard(chat_id, user_id):
    markup = types.InlineKeyboardMarkup()
    user_positions = user_data[user_id].get('positions', [])
    for position in POSITIONS:
        if position in user_positions:
            button_text = f"✅ {position}"
        else:
            button_text = position
        callback_data = f"toggle_position_{position}"
        button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
        markup.add(button)
    # Add 'Done' button
    done_button = types.InlineKeyboardButton("Done", callback_data="positions_done")
    markup.add(done_button)
    bot.send_message(chat_id, "1. Please select the position(s) you interned for. You can select multiple positions.", reply_markup=markup)

# Handle position selection callbacks
@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_position_') or call.data == 'positions_done')
def handle_position_selection(call):
    user_id = call.from_user.id
    state = user_states.get(user_id)
    if state != 'awaiting_position_selection':
        bot.answer_callback_query(call.id)
        return

    if call.data == 'positions_done':
        positions = user_data[user_id].get('positions', [])
        if positions:
            bot.send_message(call.message.chat.id, f"You have selected: {', '.join(positions)}")
            # Proceed to next question
            user_states[user_id] = 'awaiting_experience_description'
            bot.send_message(call.message.chat.id, "2. Describe the experience you gained in terms of tasks and skill development.")
        else:
            bot.send_message(call.message.chat.id, "Please select at least one position before proceeding.")
        bot.answer_callback_query(call.id)
    else:
        position = call.data.replace('toggle_position_', '')
        user_positions = user_data[user_id].get('positions', [])
        if position in user_positions:
            user_positions.remove(position)
        else:
            user_positions.append(position)
        user_data[user_id]['positions'] = user_positions
        # Update the keyboard
        markup = types.InlineKeyboardMarkup()
        for pos in POSITIONS:
            if pos in user_positions:
                button_text = f"✅ {pos}"
            else:
                button_text = pos
            callback_data = f"toggle_position_{pos}"
            button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
            markup.add(button)
        # Add 'Done' button
        done_button = types.InlineKeyboardButton("Done", callback_data="positions_done")
        markup.add(done_button)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text.startswith('Review'))
def display_review(message):
    text = message.text.strip()
    try:
        import re
        match = re.match(r"Review (\d+) from (.+)", text)
        if match:
            review_number = int(match.group(1)) - 1  # Преобразуем в индекс
            user_name = match.group(2)
            reviews = load_messages()
            user_id_found = None
            for uid, data in reviews.items():
                if data['name'] == user_name:
                    user_id_found = uid
                    break
            if user_id_found:
                user_info = reviews[user_id_found]
                user_reviews = user_info.get('reviews', [])
                if 0 <= review_number < len(user_reviews):
                    review = user_reviews[review_number]
                    positions = ', '.join(review.get('positions', []))
                    multiple_ratings = review.get('multiple_ratings', {})
                    multiple_ratings_text = '\n'.join([f"{key}: {value}/5" for key, value in multiple_ratings.items()])
                    review_message = (
                        f"Review {review_number + 1} from {user_info['name']} {user_info.get('nickname', '')}:\n"
                        f"Positions: {positions}\n"
                        f"2. Experience Description:\n{review.get('experience_description', '')}\n"
                        f"3. Satisfaction with Experience: {review.get('satisfaction_rating', '')}/5\n"
                        f"4. Team Interaction Processes: {review.get('interaction_process_rating', '')}/5\n"
                        f"5. Additional Ratings:\n{multiple_ratings_text}\n"
                        f"6. Professional Development Effect:\n{review.get('professional_development_effect', '')}\n"
                        f"7. Overall Satisfaction: {review.get('overall_satisfaction', '')}/5"
                    )
                    bot.send_message(message.chat.id, review_message, reply_markup=get_main_keyboard())
                else:
                    bot.send_message(message.chat.id, "Review not found.", reply_markup=get_main_keyboard())
            else:
                bot.send_message(message.chat.id, "User not found.", reply_markup=get_main_keyboard())
        else:
            bot.send_message(message.chat.id, "Invalid review selection.", reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error displaying review: {e}")
        bot.send_message(message.chat.id, "An error occurred while trying to display the review.", reply_markup=get_main_keyboard())

# Handle multiple ratings (placed before handle_text_messages)
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_multiple_ratings')
def handle_multiple_ratings(message):
    user_id = message.from_user.id
    text = message.text.strip()
    ratings = user_data[user_id].get('ratings_list', [])
    index = user_data[user_id].get('rating_index', 0)

    if validate_rating(text):
        key = ratings[index]
        user_data[user_id]['multiple_ratings'][key] = int(text)
        index += 1
        if index < len(ratings):
            user_data[user_id]['rating_index'] = index
            bot.send_message(
                message.chat.id,
                f"{ratings[index]}:",
                reply_markup=get_rating_keyboard()
            )
        else:
            # Proceed to next question
            user_data[user_id]['review']['multiple_ratings'] = user_data[user_id]['multiple_ratings']
            user_states[user_id] = 'awaiting_professional_development_effect'
            bot.send_message(message.chat.id, "6. What effect did the internship have on your professional development?")
    else:
        bot.send_message(message.chat.id, "Please enter a valid rating between 1 and 5.", reply_markup=get_rating_keyboard())


# Handle text messages
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    global user_states, user_data
    user_id = message.from_user.id
    text = message.text.strip()

    # If user wants to return to main menu
    if text == 'Back to main menu':
        # Reset user state and data
        user_states[user_id] = None
        user_data[user_id] = {}
        bot.send_message(message.chat.id, "Returned to the main menu.", reply_markup=get_main_keyboard())
        return

    # Get user state
    state = user_states.get(user_id)

    if state == 'awaiting_experience_description':
        user_data[user_id]['review']['experience_description'] = text
        user_states[user_id] = 'awaiting_satisfaction_rating'
        bot.send_message(
            message.chat.id,
            "3. How satisfied are you with the experience gained? Rate on a scale of 1-5 (where 1 - not satisfied at all, there was nothing useful, 5 - the experience I received completely met or exceeded my expectations).",
            reply_markup=get_rating_keyboard()
        )
    elif state == 'awaiting_satisfaction_rating':
        if validate_rating(text):
            user_data[user_id]['review']['satisfaction_rating'] = int(text)
            user_states[user_id] = 'awaiting_interaction_process_rating'
            bot.send_message(
                message.chat.id,
                "4. How well are the interaction processes built in the team? Rate on a scale of 1-5 (where 1 is very bad, nothing clear, 5 is very good and clear).",
                reply_markup=get_rating_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                "Please enter a valid rating between 1 and 5.",
                reply_markup=get_rating_keyboard()
            )
    elif state == 'awaiting_interaction_process_rating':
        if validate_rating(text):
            user_data[user_id]['review']['interaction_process_rating'] = int(text)
            # Proceed to multiple ratings
            ask_multiple_ratings(message.chat.id, user_id)
        else:
            bot.send_message(
                message.chat.id,
                "Please enter a valid rating between 1 and 5.",
                reply_markup=get_rating_keyboard()
            )
    elif state == 'awaiting_professional_development_effect':
        user_data[user_id]['review']['professional_development_effect'] = text
        user_states[user_id] = 'awaiting_overall_satisfaction_rating'
        bot.send_message(
            message.chat.id,
            "7. Overall satisfaction with the internship on a scale of 1-5 (where 1- not satisfied at all, 5 - fully satisfied).",
            reply_markup=get_rating_keyboard()
        )
    elif state == 'awaiting_overall_satisfaction_rating':
        if validate_rating(text):
            user_data[user_id]['review']['overall_satisfaction'] = int(text)
            # Save the review
            save_review(user_id, message)
        else:
            bot.send_message(
                message.chat.id,
                "Please enter a valid rating between 1 and 5.",
                reply_markup=get_rating_keyboard()
            )
    else:
        # Prompt user to use the buttons
        bot.send_message(message.chat.id, "Please use the buttons to interact with the bot.", reply_markup=get_main_keyboard())
        # Reset user state and data
        user_states[user_id] = None
        user_data[user_id] = {}

# Function to validate rating input
def validate_rating(text):
    try:
        rating = int(text)
        return 1 <= rating <= 5
    except ValueError:
        return False

# Function to ask multiple ratings
def ask_multiple_ratings(chat_id, user_id):
    user_states[user_id] = 'awaiting_multiple_ratings'
    user_data[user_id]['multiple_ratings'] = {}
    # Start with the first rating
    user_data[user_id]['rating_index'] = 0
    ratings = [
        'Working atmosphere in the team',
        'Convenience of schedule',
        'Activity of founders',
        'Activity of the whole team',
        'Opportunities for self-realization and creativity'
    ]
    user_data[user_id]['ratings_list'] = ratings  # Store ratings list in user_data
    bot.send_message(
        chat_id,
        f"5. Rate the following on a scale of 1-5 (where 1 is all very bad, 5 is very good).\n\n{ratings[0]}:",
        reply_markup=get_rating_keyboard()
    )

# Function to save the review
def save_review(user_id, message):
    user_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    nickname = f"@{message.from_user.username}" if message.from_user.username else "No username"
    review_data = user_data[user_id]['review']
    review_data['positions'] = user_data[user_id].get('positions', [])
    # Include multiple ratings
    review_data['multiple_ratings'] = user_data[user_id].get('multiple_ratings', {})
    # Load existing messages
    messages = load_messages()
    if str(user_id) not in messages:
        messages[str(user_id)] = {'name': user_name, 'nickname': nickname, 'reviews': []}
    else:
        # Update nickname if it has changed
        messages[str(user_id)]['nickname'] = nickname
    # Add new review
    messages[str(user_id)]['reviews'].append(review_data)
    # Save messages
    save_messages(messages)
    # Confirmation message
    bot.send_message(message.chat.id, 'Your review has been saved! Thank you for your feedback.', reply_markup=get_main_keyboard())
    # Reset user state and data
    user_states[user_id] = None
    user_data[user_id] = {}

# Function to display reviews
def show_reviews(chat_id):
    reviews = load_messages()
    if not reviews:
        bot.send_message(chat_id, "No reviews available.", reply_markup=get_main_keyboard())
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = []
        for user_id_key, user_info in reviews.items():
            user_name = user_info['name']
            for i, review in enumerate(user_info.get('reviews', [])):
                # Include user's name in the button text
                button_text = f"Review {i + 1} from {user_name}"
                button = types.KeyboardButton(button_text)
                buttons.append(button)
        # Arrange buttons in rows
        for i in range(0, len(buttons), 2):
            row_buttons = buttons[i:i+2]
            markup.row(*row_buttons)
        # Add 'Back to main menu' button
        back_button = types.KeyboardButton('Back to main menu')
        markup.add(back_button)
        bot.send_message(chat_id, "Select a review to read:", reply_markup=markup)

# Handle review selection

# Function to show overall summary
def show_overall_summary(chat_id):
    data = load_messages()
    # Initialize variables to calculate average ratings
    total_satisfaction_rating = 0
    total_interaction_process_rating = 0
    multiple_ratings_totals = {
        'Working atmosphere in the team': 0,
        'Convenience of schedule': 0,
        'Activity of founders': 0,
        'Activity of the whole team': 0,
        'Opportunities for self-realization and creativity': 0
    }
    count_satisfaction_rating = 0
    count_interaction_process_rating = 0
    counts_multiple_ratings = {key: 0 for key in multiple_ratings_totals}

    # Iterate through all reviews to sum ratings
    for user_info in data.values():
        for review in user_info.get('reviews', []):
            if 'satisfaction_rating' in review:
                total_satisfaction_rating += review['satisfaction_rating']
                count_satisfaction_rating += 1
            if 'interaction_process_rating' in review:
                total_interaction_process_rating += review['interaction_process_rating']
                count_interaction_process_rating += 1
            multiple_ratings = review.get('multiple_ratings', {})
            for key in multiple_ratings_totals.keys():
                if key in multiple_ratings:
                    multiple_ratings_totals[key] += multiple_ratings[key]
                    counts_multiple_ratings[key] += 1

    # Calculate averages
    summary_message = "Overall Summary:\n"
    if count_satisfaction_rating > 0:
        avg_satisfaction = total_satisfaction_rating / count_satisfaction_rating
        summary_message += f"Average Satisfaction with Experience: {avg_satisfaction:.2f}/5\n"
    else:
        summary_message += "No data for Satisfaction with Experience\n"

    if count_interaction_process_rating > 0:
        avg_interaction = total_interaction_process_rating / count_interaction_process_rating
        summary_message += f"Average Team Interaction Processes: {avg_interaction:.2f}/5\n"
    else:
        summary_message += "No data for Team Interaction Processes\n"

    summary_message += "Average Ratings for Additional Criteria:\n"
    for key in multiple_ratings_totals.keys():
        if counts_multiple_ratings[key] > 0:
            avg = multiple_ratings_totals[key] / counts_multiple_ratings[key]
            summary_message += f"{key}: {avg:.2f}/5\n"
        else:
            summary_message += f"{key}: No data\n"

    bot.send_message(chat_id, summary_message, reply_markup=get_main_keyboard())

if __name__ == '__main__':
    init_data_file()
    bot.infinity_polling()