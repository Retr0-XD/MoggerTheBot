import os
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from providers import TorrentProvider, NSFWProvider, TeraBoxProvider, InstagramProvider
from config import TELEGRAM_TOKEN, NSFW_WHITELIST, ADMIN_ID
from access_tracker import AccessTracker

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables!")

class MediaBot:
    def __init__(self):
        self.torrent = TorrentProvider()
        self.nsfw = NSFWProvider()
        self.terabox = TeraBoxProvider()
        self.instagram = InstagramProvider()
        self.access_tracker = AccessTracker()
        
    def setup(self):
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Register command handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('torrent', self.search_torrent))
        application.add_handler(CommandHandler('terabox', self.terabox_download))
        application.add_handler(CommandHandler('instagram', self.instagram_download))
        application.add_handler(CommandHandler('ph_search', self.search_pornhub))
        application.add_handler(CommandHandler('hq_search', self.search_hqporner))
        application.add_handler(CommandHandler('ph_stars', self.get_pornhub_stars))
        application.add_handler(CommandHandler('hq_actress', self.get_hqporner_actress_videos))
        application.add_handler(CommandHandler('xvideos_search', self.search_xvideos))
        application.add_handler(CommandHandler('change_site', self.change_torrent_site))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        return application
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        user = update.effective_user
        welcome_text = (
            f"🌟 *Welcome {user.first_name} to MoggerTheBot!* 🌟\n\n"
            "I'm your powerful media companion, ready to help you search and download content!\n\n"
            
            "🎯 *Core Features*\n"
            "━━━━━━━━━━━━━━━━\n"
            "🔍 *Search & Download*\n"
            "• `/torrent <query>` - Search torrents across multiple sites\n"
            "• `/change_site` - View & change torrent sites\n"
            "• `/terabox <url>` - Download from TeraBox\n"
            "• `/instagram <url>` - Download from Instagram\n\n"
            
            "🔞 *NSFW Features* (Auth Required)\n"
            "• `/ph_search <query>` - PornHub search\n"
            "• `/ph_stars` - Browse PornHub stars\n"
            "• `/hq_search <query>` - HQPorner search\n"
            "• `/hq_actress <name>` - Search by actress\n"
            "• `/xvideos_search <query>` - XVideos search\n\n"
            
            "📊 *Daily Rate Limits*\n"
            "━━━━━━━━━━━━━━━━\n"
            "• 🔄 Torrent API: 100 searches\n"
            "• 📦 TeraBox API: 50 downloads\n"
            "• 📸 Instagram API: 100 requests\n"
            "• 🎥 NSFW APIs: 100 requests\n\n"
            
            "💡 *Pro Tips*\n"
            "━━━━━━━━━━━━━━━━\n"
            "• Use specific search terms\n"
            "• Magnet links are in `code blocks` - easy to copy!\n"
            "• Try different torrent sites for more results\n"
            "• Check file size before downloading\n\n"
            
            "⚡ *Quick Links*\n"
            "━━━━━━━━━━━━━━━━\n"
            "• Contact: @Retr0XD\n"
            "• Support Group: Coming soon!\n\n"
            
            "🎮 *Ready to start?*\n"
            "Try `/torrent batman` to test the search!\n\n"
            
            "_Made with ❤️ by @Retr0XD_"
        )
        
        try:
            await update.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        except Exception as e:
            # Fallback without markdown if parsing fails
            await update.message.reply_text(
                welcome_text.replace('*', '').replace('`', '').replace('_', ''),
                disable_web_page_preview=True
            )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await self.start(update, context)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == 'nsfw':
            user_id = update.effective_user.id
            has_access = user_id in NSFW_WHITELIST
            
            if not has_access:
                # Record unauthorized attempt
                self.access_tracker.record_attempt(
                    user_id=user_id,
                    username=update.effective_user.username,
                    first_name=update.effective_user.first_name
                )
                keyboard = [
                    [InlineKeyboardButton("« Back", callback_data='back')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(
                    "⚠️ Access Denied: You are not authorized to access NSFW content.\n"
                    "Contact the bot administrator for access.\n\n"
                    "Required: Your Telegram ID must be in the whitelist.\n"
                    "Contact the gigachad retr0 for access\n"
                    f"Your ID: {update.effective_user.id}",
                    reply_markup=reply_markup
                )
                return
                
            keyboard = [
                [InlineKeyboardButton("Search PornHub", callback_data='ph_search'),
                 InlineKeyboardButton("Search HQPorner", callback_data='hq_search')],
                [InlineKeyboardButton("PornHub Stars", callback_data='ph_stars'),
                 InlineKeyboardButton("HQPorner Actress", callback_data='hq_actress')],
                [InlineKeyboardButton("Search XVideos", callback_data='xvideos_search')],
                [InlineKeyboardButton("« Back", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("Choose NSFW Option:", reply_markup=reply_markup)
        elif query.data == 'view_attempts':
            if update.effective_user.id == ADMIN_ID:  
                attempts = self.access_tracker.get_all_attempts()
                if not attempts:
                    await query.message.edit_text(
                        "No unauthorized access attempts recorded.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='back')]])
                    )
                    return
                    
                response = "Unauthorized Access Attempts:\n\n"
                for user_id, data in attempts.items():
                    response += f"User ID: {user_id}\n"
                    response += f"Username: @{data['username']}\n" if data['username'] else "Username: N/A\n"
                    response += f"Name: {data['first_name']}\n" if data['first_name'] else "Name: N/A\n"
                    response += f"Total Attempts: {data['total_attempts']}\n"
                    response += f"Last Attempt: {data['last_attempt']}\n\n"
                    
                # Split response if too long
                if len(response) > 4000:
                    response = response[:4000] + "\n\n[List truncated due to length]"
                    
                await query.message.edit_text(
                    response,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='back')]])
                )
            else:
                await query.message.edit_text(
                    "⚠️ Access Denied: Only administrators can view access attempts.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data='back')]])
                )
        elif query.data == 'search_torrent':
            current_site = self.torrent.get_current_site_info()
            await query.message.reply_text(
                f"Current torrent site: {current_site['title']} ({current_site['code']})\n"
                "Send me the name of the movie/series to search for torrents.\n"
                "Format: /torrent movie_name"
            )
        elif query.data == 'change_site':
            sites = self.torrent.get_available_sites()
            current_site = self.torrent.get_current_site_info()
            
            # Create a grid of 2 buttons per row
            keyboard = []
            row = []
            for site in sites:
                button = InlineKeyboardButton(
                    f"{site['title']} ({site['code']})",
                    callback_data=f"site_{site['id']}"
                )
                row.append(button)
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            
            if row:  # Add any remaining buttons
                keyboard.append(row)
                
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"Current site: {current_site['title']} ({current_site['code']})\n"
                "Choose a torrent site:",
                reply_markup=reply_markup
            )
        elif query.data.startswith('site_'):
            site = query.data.replace('site_', '')
            if self.torrent.set_site(site):
                current_site = self.torrent.get_current_site_info()
                await query.message.reply_text(
                    f"Torrent site changed to: {current_site['title']} ({current_site['code']})"
                )
            else:
                await query.message.reply_text("Invalid torrent site!")
        elif query.data == 'terabox':
            await query.message.reply_text(
                "Send me the TeraBox URL to download.\n"
                "Format: /terabox <url>\n"
                "Example: /terabox https://www.terabox.app/sharing/link?surl=xxx"
            )
        elif query.data == 'instagram':
            await query.message.reply_text(
                "Send me the Instagram URL to download.\n"
                "Format: /instagram <url>\n"
                "Example: /instagram https://www.instagram.com/reel/xxx\n"
                "Supports: Posts, Reels, IGTV"
            )
        elif query.data == 'ph_search':
            await query.message.reply_text(
                "Send me what to search on PornHub\n"
                "Format: /ph_search query"
            )
        elif query.data == 'hq_search':
            await query.message.reply_text(
                "Send me what to search on HQPorner\n"
                "Format: /hq_search query"
            )
        elif query.data == 'ph_stars':
            await query.message.reply_text(
                "Get popular PornHub stars\n"
                "Format: /ph_stars [limit]"
            )
        elif query.data == 'hq_actress':
            await query.message.reply_text(
                "Get videos by actress on HQPorner\n"
                "Format: /hq_actress actress_name"
            )
        elif query.data == 'xvideos_search':
            await query.message.reply_text(
                "Send me what to search on XVideos\n"
                "Format: /xvideos_search query"
            )

    async def change_torrent_site(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            sites = self.torrent.get_available_sites()
            current = self.torrent.get_current_site_info()
            
            response = "Available torrent sites:\n\n"
            for site in sites:
                status = "✅ CURRENT" if site['id'] == current['id'] else ""
                response += f"• {site['title']} ({site['id']}) {status}\n"
            
            response += "\nTo change site, use: /change_site <site_id>"
            await update.message.reply_text(response)
            return
            
        site_id = context.args[0].lower()
        if self.torrent.set_site(site_id):
            site_info = self.torrent.get_current_site_info()
            await update.message.reply_text(
                f"✅ Changed torrent site to: {site_info['title']} ({site_info['id']})"
            )
        else:
            await update.message.reply_text(
                "❌ Invalid site ID. Use /change_site to see available sites."
            )

    async def check_nsfw_access(self, update: Update) -> bool:
        """Check if user has access to NSFW content"""
        user = update.effective_user
        user_id = user.id
        has_access = user_id in NSFW_WHITELIST
        
        if not has_access:
            # Record unauthorized attempt
            self.access_tracker.record_attempt(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name
            )
            await update.message.reply_text(
                "⚠️: You are not authorized to access NSFW content.\n"
                "Contact the gigichad retr0 for access."
            )
        return has_access

    async def search_torrent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Please provide a search query!\n"
                "Format: /torrent <query>"
            )
            return
            
        query = ' '.join(context.args)
        await update.message.reply_text(f"🔍 Searching for: {query}")
        
        results = await self.torrent.search(query)
        
        if not results:
            await update.message.reply_text(
                "❌ No results found or an error occurred.\n"
                "Try changing the torrent site with /change_site <site_id>"
            )
            return
            
        # Group results by movie/content
        grouped_results = {}
        for result in results:
            title = result['title'].split('(')[0].strip()  # Base title without quality
            if title not in grouped_results:
                grouped_results[title] = {
                    'info': result,
                    'versions': []
                }
            grouped_results[title]['versions'].append(result)
            
        for title, data in grouped_results.items():
            info = data['info']
            
            # Movie Information
            response = [
                f"🎬 *{title}*\n"
            ]
            
            if 'rating' in info:
                response.append(f"⭐ Rating: {info['rating']}")
            if 'genre' in info:
                response.append(f"🎭 Genre: {info['genre']}")
            if 'runtime' in info:
                response.append(f"⏱️ Runtime: {info['runtime']}")
            if 'uploadDate' in info:
                response.append(f"📅 Year: {info['uploadDate']}")
            if 'description' in info:
                response.append(f"📝 Description: {info['description']}")
                
            response.append("\n📥 Available Versions:")
            
            # Add each version with full details
            for version in data['versions']:
                version_info = [
                    f"\n▫️ Quality: {version.get('quality', 'N/A')}",
                    f"▫️ Type: {version.get('type', 'N/A')}",
                    f"▫️ Size: {version.get('size', 'N/A')}"
                ]
                response.append("\n".join(version_info))
                
                if version.get('magnet'):
                    response.append(f"🧲 Magnet Link:\n`{version['magnet']}`")
                if version.get('url'):
                    response.append(f"🔗 URL: {version['url']}")
                response.append("")  # Add spacing between versions
                
            response.append("\n━━━━━━━━━━━━━━━━━━━━━━\n")
            
            # Join all parts and send
            full_response = "\n".join(response)
            
            # Split message if it's too long for Telegram's limit (4096 characters)
            if len(full_response) > 4096:
                parts = [full_response[i:i+4096] for i in range(0, len(full_response), 4096)]
                for part in parts:
                    try:
                        await update.message.reply_text(
                            part,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                    except Exception as e:
                        # Fallback without markdown if parsing fails
                        await update.message.reply_text(
                            part.replace('*', '').replace('`', ''),
                            disable_web_page_preview=True
                        )
            else:
                try:
                    await update.message.reply_text(
                        full_response,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    # Fallback without markdown if parsing fails
                    await update.message.reply_text(
                        full_response.replace('*', '').replace('`', ''),
                        disable_web_page_preview=True
                    )

    async def search_pornhub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_nsfw_access(update):
            return
            
        if not context.args:
            await update.message.reply_text("Please provide a search query!")
            return
        
        query = ' '.join(context.args)
        results = await self.nsfw.search_pornhub(query)
        
        if not results:
            await update.message.reply_text("No videos found!")
            return
        
        response = "Found videos on PornHub:\n\n"
        for idx, video in enumerate(results, 1):
            response += f"{idx}. {video['title']}\n"
            response += f"Duration: {video['duration']}\n"
            response += f"Views: {video['views']} | Rating: {video['rating']}\n"
            response += f"URL: {video['url']}\n\n"
            
        await update.message.reply_text(response)

    async def search_hqporner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_nsfw_access(update):
            return
            
        if not context.args:
            await update.message.reply_text("Please provide a search query!")
            return
        
        query = ' '.join(context.args)
        results = await self.nsfw.search_hqporner(query)
        
        if not results:
            await update.message.reply_text("No videos found!")
            return
        
        response = "Found videos on HQPorner:\n\n"
        for idx, video in enumerate(results, 1):
            response += f"{idx}. {video['title']}\n"
            response += f"Duration: {video['duration']}\n"
            response += f"Quality: {video['quality']}\n"
            response += f"URL: {video['url']}\n\n"
            
        await update.message.reply_text(response)

    async def get_pornhub_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_nsfw_access(update):
            return
            
        stars = await self.nsfw.get_pornhub_stars()
        
        if not stars:
            await update.message.reply_text("No stars found!")
            return
        
        response = "Popular PornHub Stars:\n\n"
        for idx, star in enumerate(stars, 1):
            response += f"{idx}. {star['name']}\n"
            response += f"Rank: {star['rank']}\n"
            response += f"Videos: {star['videos']} | Views: {star['views']}\n"
            response += f"URL: {star['url']}\n\n"
            
        await update.message.reply_text(response)

    async def get_hqporner_actress_videos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_nsfw_access(update):
            return
            
        if not context.args:
            await update.message.reply_text("Please provide an actress name!")
            return
        
        actress = ' '.join(context.args)
        results = await self.nsfw.get_hqporner_actress_videos(actress)
        
        if not results:
            await update.message.reply_text("No videos found for this actress!")
            return
        
        response = f"Found videos for {actress} on HQPorner:\n\n"
        for idx, video in enumerate(results, 1):
            response += f"{idx}. {video['title']}\n"
            response += f"Duration: {video['duration']}\n"
            response += f"Quality: {video['quality']}\n"
            response += f"URL: {video['url']}\n\n"
            
        await update.message.reply_text(response)

    async def search_xvideos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search videos on XVideos"""
        if not await self.check_nsfw_access(update):
            return
            
        if not context.args:
            await update.message.reply_text("Please provide a search query!")
            return
            
        query = ' '.join(context.args)
        await update.message.reply_text(f"Searching XVideos for: {query}")
        
        results = await self.nsfw.search_xvideos(query)
        
        if not results:
            await update.message.reply_text("No results found or an error occurred.")
            return
            
        response = "Search Results:\n\n"
        for idx, video in enumerate(results, 1):
            response += f"{idx}. {video['title']}\n"
            response += f"Duration: {video['duration']}\n"
            response += f"Quality: {video['quality']}\n"
            response += f"URL: {video['url']}\n\n"
            
        # Split response if too long
        if len(response) > 4000:
            response = response[:4000] + "\n\n[Results truncated due to length]"
            
        await update.message.reply_text(response)

    async def terabox_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Please provide a TeraBox URL!\n"
                "Usage: /terabox <url>\n"
                "Example: /terabox https://www.terabox.app/sharing/link?surl=xxx"
            )
            return
            
        url = context.args[0]
        if not ('terabox.app' in url or 'terabox.com' in url):
            await update.message.reply_text("Please provide a valid TeraBox URL!")
            return
            
        await update.message.reply_text("Processing your TeraBox download request...")
        
        try:
            result = await self.terabox.get_download_link(url)
            if result.get('error'):
                await update.message.reply_text(f"Error: {result['error']}")
                return
                
            if result.get('download_url'):
                await update.message.reply_text(f"Download URL: {result['download_url']}")
            else:
                await update.message.reply_text("Failed to get download link. Please try again later.")
        except Exception as e:
            await update.message.reply_text(f"Error processing your request: {str(e)}")

    async def instagram_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Please provide an Instagram URL!\n"
                "Usage: /instagram <url>\n"
                "Example: /instagram https://www.instagram.com/reel/xxx\n"
                "Supports: Posts, Reels, IGTV"
            )
            return
            
        url = context.args[0]
        if not ('instagram.com' in url):
            await update.message.reply_text("Please provide a valid Instagram URL!")
            return
            
        await update.message.reply_text("Processing your Instagram download request...")
        
        try:
            # Determine content type
            content_type = 'reel' if '/reel/' in url else 'post'
            if '/tv/' in url:
                content_type = 'igtv'
                
            result = await self.instagram.get_media(url, content_type)
            if result.get('error'):
                await update.message.reply_text(f"Error: {result['error']}")
                return
                
            if result.get('download_url'):
                await update.message.reply_text(f"Download URL: {result['download_url']}")
            elif result.get('urls'):
                response = "Download URLs:\n"
                for idx, url in enumerate(result['urls'], 1):
                    response += f"\n{idx}. {url}"
                await update.message.reply_text(response)
            else:
                await update.message.reply_text("Failed to get download link. Please try again later.")
        except Exception as e:
            await update.message.reply_text(f"Error processing your request: {str(e)}")

    def run(self):
        app = self.setup()
        app.run_polling()

if __name__ == '__main__':
    bot = MediaBot()
    bot.run()
