from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

router = Router()


@router.message(CommandStart())
async def start_command_handler(message: Message):
    await message.answer("Salam")


@router.message(Command("help"))
async def help_command_handler(message: Message):
    await message.answer("Send me location send me location then i will help you")