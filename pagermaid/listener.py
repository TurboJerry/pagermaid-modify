import sys
from time import strftime, gmtime, time
from traceback import format_exc

from pyrogram import ContinuePropagation, StopPropagation, filters, Client
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import (
    MessageIdInvalid,
    MessageNotModified,
    MessageEmpty,
    UserNotParticipant
)
from pyrogram.handlers import MessageHandler

from pagermaid import help_messages, logs, Config, bot
from pagermaid.utils import lang, attach_report


def noop(*args, **kw):
    pass


def listener(**args):
    """ Register an event listener. """
    command = args.get('command', None)
    description = args.get('description', None)
    parameters = args.get('parameters', None)
    pattern = args.get('pattern', None)
    diagnostics = args.get('diagnostics', True)
    ignore_edited = args.get('ignore_edited', False)
    is_plugin = args.get('is_plugin', True)
    owners_only = args.get("owners_only", False)
    admins_only = args.get("admins_only", False)
    groups_only = args.get("groups_only", False)

    if command is not None:
        if command in help_messages:
            raise ValueError(f"{lang('error_prefix')} {lang('command')} \"{command}\" {lang('has_reg')}")
        pattern = fr"^,{command}(?: |$)([\s\S]*)"
    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = f"(?i){pattern}"
    else:
        args['pattern'] = pattern
    base_filters = (
            filters.me
            & filters.regex(args['pattern'])
            & ~filters.via_bot
            & ~filters.forwarded
    )
    if ignore_edited:
        base_filters &= ~filters.edited
    if 'ignore_edited' in args:
        del args['ignore_edited']
    if 'command' in args:
        del args['command']
    if 'diagnostics' in args:
        del args['diagnostics']
    if 'description' in args:
        del args['description']
    if 'parameters' in args:
        del args['parameters']
    if 'is_plugin' in args:
        del args['is_plugin']
    if 'owners_only' in args:
        del args['owners_only']
    if 'admins_only' in args:
        del args['admins_only']
    if 'groups_only' in args:
        del args['groups_only']

    def decorator(function):

        async def handler(client: Client, message: Message):
            message.client = client

            try:
                try:
                    parameter = message.matches[0].group(1).split(' ')
                    if parameter == ['']:
                        parameter = []
                    message.parameter = parameter
                    message.arguments = message.matches[0].group(1)
                except BaseException:
                    message.parameter = None
                    message.arguments = None
                await function(client, message)
            except StopPropagation:
                raise StopPropagation
            except KeyboardInterrupt:
                pass
            except MessageNotModified:
                pass
            except MessageIdInvalid:
                logs.warning(
                    "Please Don't Delete Commands While it's Processing.."
                )
            except UserNotParticipant:
                pass
            except ContinuePropagation:
                raise ContinuePropagation
            except SystemExit:
                exit(1)
            except BaseException:
                exc_info = sys.exc_info()[1]
                exc_format = format_exc()
                try:
                    await message.reply(lang('run_error'), quote=True)
                except BaseException:
                    pass
                if not diagnostics:
                    return
                if Config.ERROR_REPORT:
                    report = f"# Generated: {strftime('%H:%M %d/%m/%Y', gmtime())}. \n" \
                             f"# ChatID: {message.chat.id}. \n" \
                             f"# UserID: {message.from_user.id if message.from_user else message.sender_chat.id}. \n" \
                             f"# Message: \n-----BEGIN TARGET MESSAGE-----\n" \
                             f"{message.text if message.text else message.caption}\n-----END TARGET MESSAGE-----\n" \
                             f"# Traceback: \n-----BEGIN TRACEBACK-----\n" \
                             f"{str(exc_format)}\n-----END TRACEBACK-----\n" \
                             f"# Error: \"{str(exc_info)}\". \n"
                    await attach_report(report, f"exception.{time()}.pagermaid", None,
                                        "Error report generated.")

        bot.add_handler(MessageHandler(handler, filters=base_filters), group=0)

        return handler

    if description is not None and command is not None:
        if parameters is None:
            parameters = ""
        help_messages.update({
            f"{command}": f"**{lang('use_method')}:** `-{command} {parameters}`\
                \n{description}"
        })

    return decorator


def raw_listener(filter_s):
    """Simple Decorator To Handel Custom Filters"""
    def decorator(function):
        async def handler(client, message):
            try:
                await function(client, message)
            except StopPropagation:
                raise StopPropagation
            except ContinuePropagation:
                raise ContinuePropagation
            except UserNotParticipant:
                pass
            except MessageEmpty:
                pass
            except BaseException:
                exc_info = sys.exc_info()[1]
                exc_format = format_exc()
                try:
                    await message.reply(lang('run_error'), quote=True)
                except BaseException:
                    pass
                if Config.ERROR_REPORT:
                    report = f"# Generated: {strftime('%H:%M %d/%m/%Y', gmtime())}. \n" \
                             f"# ChatID: {message.chat.id}. \n" \
                             f"# UserID: {message.from_user.id if message.from_user else message.sender_chat.id}. \n" \
                             f"# Message: \n-----BEGIN TARGET MESSAGE-----\n" \
                             f"{message.text}\n-----END TARGET MESSAGE-----\n" \
                             f"# Traceback: \n-----BEGIN TRACEBACK-----\n" \
                             f"{str(exc_format)}\n-----END TRACEBACK-----\n" \
                             f"# Error: \"{str(exc_info)}\". \n"
                    await attach_report(report, f"exception.{time()}.pagermaid", None,
                                        "Error report generated.")
                message.continue_propagation()

        bot.add_handler(MessageHandler(handler, filters=filter_s), group=0)

        return handler

    return decorator
