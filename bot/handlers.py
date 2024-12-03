import os
import io
import PyPDF2
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Conversation states
CHOOSE_SERVICE, AWAITING_DOCUMENT, AWAITING_STRATEGY = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bot and present service options."""
    keyboard = [
        ['📄 Case Study Insights', '🔍 Strategy Review'],
        ['🔥 Marketing Plan Roast', '🚀 Campaign Analysis']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Welcome to the Marketing AI Assistant! What would you like to do?", 
        reply_markup=reply_markup
    )
    return CHOOSE_SERVICE

async def analyze_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt_type: str) -> None:
    """Generic AI analysis method."""
    # Download the file
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    
    # Read PDF
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Truncate text if too long
    text = text[:10000]  # Limit to prevent token overflow
    
    # Generate analysis using Groq
    try:
        prompt_templates = {
            'Case Study Insights': "Analyze this marketing case study and provide:\n1. A concise summary\n2. Key strategic insights\n3. Potential learnings for other businesses",
            'Strategy Review': "Review this marketing strategy and provide:\n1. Strengths and weaknesses\n2. Potential improvements\n3. Strategic recommendations",
            'Marketing Plan Roast': "Provide a BRUTALLY sarcastic and hilarious critique of this marketing plan. Channel your inner comedy roast master while dissecting the strategy. Include:\n1. Savage takedowns of the most ridiculous assumptions\n2. Comedic red flags that scream 'marketing disaster'\n3. Witty, razor-sharp observations that would make a stand-up comedian proud\n4. Laugh-out-loud predictions of spectacular failure\n\nRoast this plan like it's the worst comedy special in marketing history!",
            'Campaign Analysis': "Analyze this marketing campaign document and provide:\n1. Campaign effectiveness assessment\n2. Key performance indicators\n3. Recommendations for optimization"
        }
        
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are an expert marketing strategist."},
                {"role": "user", "content": f"{prompt_templates.get(prompt_type, 'Analyze the following document:')}\n\nDocument:\n{text}"}
            ]
        )
        
        analysis = response.choices[0].message.content
        
        # Split response if too long for Telegram
        if len(analysis) > 4096:
            for x in range(0, len(analysis), 4096):
                await update.message.reply_text(analysis[x:x+4096])
        else:
            await update.message.reply_text(analysis)
        
        # Return to main menu
        keyboard = [
            ['📄 Case Study Insights', '🔍 Strategy Review'],
            ['🔥 Marketing Plan Roast', '🚀 Campaign Analysis']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "What would you like to do next?", 
            reply_markup=reply_markup
        )
        return CHOOSE_SERVICE
    
    except Exception as e:
        await update.message.reply_text(f"An error occurred during analysis: {str(e)}")
        return ConversationHandler.END

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle service selection and prompt for document upload."""
    service = update.message.text
    context.user_data['selected_service'] = service
    
    await update.message.reply_text(
        f"You selected: {service}\nPlease upload a PDF document for analysis.",
        reply_markup=ReplyKeyboardRemove()
    )
    return AWAITING_DOCUMENT

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle document upload and analyze based on selected service."""
    service = context.user_data.get('selected_service')
    
    if service == '📄 Case Study Insights':
        return await analyze_with_ai(update, context, 'Case Study Insights')
    elif service == '🔍 Strategy Review':
        return await analyze_with_ai(update, context, 'Strategy Review')
    elif service == '🔥 Marketing Plan Roast':
        return await analyze_with_ai(update, context, 'Marketing Plan Roast')
    elif service == '🚀 Campaign Analysis':
        return await analyze_with_ai(update, context, 'Campaign Analysis')

def setup_handlers(application: Application) -> None:
    """Sets up the conversation handlers for the bot."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            CHOOSE_SERVICE: [
                MessageHandler(
                    filters.Regex('^(📄 Case Study Insights|🔍 Strategy Review|🔥 Marketing Plan Roast|🚀 Campaign Analysis)$'), 
                    handle_service_selection
                )
            ],
            AWAITING_DOCUMENT: [
                MessageHandler(filters.Document.PDF, handle_document)
            ]
        },
        fallbacks=[CommandHandler("start", start_command)]
    )
    
    application.add_handler(conv_handler)