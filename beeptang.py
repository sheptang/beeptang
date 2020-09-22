import os, random, threading, time, asyncio, re, spotipy, requests
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
from random import randrange
from time import sleep
from twitchio.ext import commands

beeptang = commands.Bot(
    irc_token=os.environ["TMI_TOKEN"],
    client_id=os.environ["CLIENT_ID"],
    nick=os.environ["BOT_NICK"],
    prefix=os.environ["BOT_PREFIX"],
    initial_channels=[os.environ["CHANNEL"]]
)

spotify_scope = "user-read-playback-state user-read-currently-playing user-modify-playback-state"

spotifyAuth = SpotifyOAuth(
    client_id=os.environ["SPOTIPY_CLIENT_ID"],
    client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
    redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
    scope=spotify_scope,
    username="sheptang"
)

giveaway_list = []
giveaway_winner_arr = []
survey_votes = []
survey_options = []
songreq_list = []
confirmed_songreq_list = []
giveaway_trigger = False
giveaway_on = False
survey_on = False
songreq_on = True
special_ignore_list = []
# special_ignore_list: banned from using beeptang
generic_ignore_list = ["beeptang", "moobot"]
# generic_ignore_list: prevent accidental command triggering
mod_username_list = ["camperxl", "themightykebap", "realgoku", "sheptang", "sh1nax"]
beep_list = ["beep boop", "boop beep", "send halp", "salın beni", "boş yapma anıl", "ayranı içen yoksa döküyorum", "anılın bilgisayarında hapsoldum yardım edin aq"]

try:
    spoti_token = spotifyAuth.get_cached_token()
except:
    spoti_token = ""


def reset_giveaway_list():
    global giveaway_list
    global giveaway_on
    giveaway_list = []
    giveaway_on = False


def reset_survey_list():
    global survey_votes
    global survey_options
    global survey_on
    survey_votes = []
    survey_options = []
    survey_on = False


def find_rec_len_survey_opt(ind):
    global survey_votes
    return len(survey_votes[ind])


def pause_songreq_list():
    global songreq_on
    songreq_on = False


def resume_songreq_list():
    global songreq_on
    songreq_on = True


def reset_songreq_list():
    global songreq_list
    songreq_list = []


def reset_confirmed_songreq_list():
    global confirmed_songreq_list
    confirmed_songreq_list = []


def find_whole_word(w, string):
    pattern = re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE)
    if pattern.search(string):
        return True
    else:
        return False


async def tryFetchSpotiToken():
    global spoti_token, spoti
    if (not spoti_token) or (spoti_token is None):
        spoti_auth_token = spotifyAuth.get_authorize_url()
        ht_spoti_auth_req = requests.get(spoti_auth_token, allow_redirects=True)
        ht_spoti_auth_resp = ht_spoti_auth_req.url
        ht_spoti_auth_resp_code = spotifyAuth.parse_response_code(ht_spoti_auth_resp)
        spotifyAuth.get_access_token(ht_spoti_auth_resp_code)
        spoti_token = spotifyAuth.get_cached_token()
    elif spotifyAuth.is_token_expired(spotifyAuth.get_cached_token()):
        spoti_token = spotifyAuth.refresh_access_token(spoti_token["refresh_token"])
    else:
        spoti_token = spotifyAuth.get_cached_token()
    spoti = spotipy.Spotify(auth=spoti_token["access_token"])


@beeptang.event
async def event_ready():

    print("beeptang ready.")

    ws = beeptang._ws

    await tryFetchSpotiToken()

    while True:
        await ws.send_privmsg(os.environ['CHANNEL'], f"/me - {beep_list[randrange(len(beep_list))]}")
        await asyncio.sleep(420)


@beeptang.event
async def event_message(ctx):
    global giveaway_winner_arr, giveaway_timeout, giveaway_count, giveaway_results, giveaway_repetitive, ga_announce_subject, ga_announce_count, giveaway_list, giveaway_on, survey_on, survey_votes, survey_options, try_sv_exist, songreq_list, songreq_on, confirmed_songreq_list
    message_content = ctx.content

    possible_command = message_content.split()[0].lower()
    possible_command_issuer = ctx.author.name.lower()

    if ctx.author.name.lower() in generic_ignore_list or ctx.author.name.lower() in special_ignore_list:
        return

    async def replaceTimeString(time_string):
        time_conversion = [("years", "yıl"), ("year", "yıl"), ("months", "ay"), ("month", "ay"), ("weeks", "hafta"), ("week", "hafta"), ("days", "gün"), ("day", "gün"), ("hours", "saat"), ("hour", "saat"), ("minutes", "dakika"), ("minute", "dakika"), ("seconds", "saniye"), ("second", "saniye")]
        for search, replacement in time_conversion:
            time_string = time_string.replace(search, replacement)
        return time_string

    async def gaEngine(giveaway_params):
        global giveaway_timeout, giveaway_count, giveaway_results, giveaway_repetitive, giveaway_on
        if not giveaway_on:
            reset_giveaway_list()
            giveaway_winner_arr = []
            if len(giveaway_params) < 4 and giveaway_params[0].strip() != "!gaAnnounce":
                await ctx.channel.send("/me - kendi yazdığın komutu yanlış kullandın ey sahip · !gaStart *çekiliş[str] *süre[sec] *adet[int] tekrarlı[bool] sonuçlar[bool]")
                giveaway_on = False
            elif len(giveaway_params) >= 4 or giveaway_params[0].strip() == "!gaAnnounce":
                try:
                    giveaway_subject = giveaway_params[1]
                except:
                    giveaway_subject = "???"
                try:
                    giveaway_timeout = int(giveaway_params[2])
                except (TypeError, IndexError):
                    giveaway_timeout = 90
                try:
                    giveaway_count = int(giveaway_params[3])
                except (TypeError, IndexError):
                    giveaway_count = 1
                try:
                    giveaway_repetitive = bool(giveaway_params[4])
                except (TypeError, IndexError):
                    giveaway_repetitive = False
                try:
                    giveaway_results = bool(giveaway_params[5])
                except (TypeError, IndexError):
                    giveaway_results = True
                giveaway_on = True
                await ctx.channel.send(
                    f"/me - çekiliş başladı ey sahip! · çekiliş: {giveaway_subject} · süre: {giveaway_timeout} sn · çekiliş adedi: {giveaway_count}")
            giveaway_countdown_multiplier = 0
            while giveaway_on:
                giveaway_time_left = int(giveaway_timeout) - giveaway_countdown_multiplier
                await asyncio.sleep(1)
                giveaway_countdown_multiplier += 1
                if giveaway_time_left == 0 or giveaway_time_left < 0:
                    await ctx.channel.send("/me - çekiliş sona erdi!")
                    if len(giveaway_list) >= 2:
                        keep_rolling = True
                        while keep_rolling:
                            await asyncio.sleep(1)
                            random_winner = randrange(0, len(giveaway_list))
                            await ctx.channel.send("/me - zar atıldı.")
                            if not giveaway_repetitive:
                                if giveaway_list[random_winner].lower() not in giveaway_winner_arr:
                                    giveaway_winner_arr.append(giveaway_list[random_winner])
                            else:
                                giveaway_winner_arr.append(giveaway_list[random_winner])
                            if len(giveaway_winner_arr) == int(giveaway_count):
                                keep_rolling = False
                        giveaway_on = False
                        i_winner = 1
                        while i_winner < len(giveaway_winner_arr):
                            giveaway_winner_arr[i_winner] = "@" + giveaway_winner_arr[i_winner]
                            i_winner += 1
                        if not giveaway_results:
                            giveaway_results_file = open("giveaway_results.txt", "w")
                            linified_winners = "\n ".join(map(str, giveaway_winner_arr))
                            giveaway_results_file.write(linified_winners)
                            giveaway_results_file.close()
                        elif giveaway_results:
                            stringed_winners = ", ".join(map(str, giveaway_winner_arr))
                            await ctx.channel.send(f"/me - kazananlar: @{stringed_winners}")
                    elif len(giveaway_list) < 2:
                        giveaway_on = False
                        await ctx.channel.send("/me - katılım sayısı ikiden az olduğu için çekiliş iptal edildi.")
                elif (giveaway_time_left % 30 == 0 or giveaway_time_left == 10 or (
                        6 > giveaway_time_left > 0)) and giveaway_time_left < int(giveaway_timeout):
                    await ctx.channel.send(f"/me - çekilişin sona ermesine {giveaway_time_left} sn kaldı!")

    async def svEngine(survey_params):
        global survey_on, survey_timeout, survey_options
        if len(survey_params) <= 3:
            await ctx.channel.send(
                "/me - kendi yazdığın komutu yanlış kullandın ey sahip · !svAnnounce *konu[str] *süre[sec] *args[]")
            survey_on = False
        elif len(survey_params) > 3:
            try:
                survey_subject = survey_params[1]
            except:
                survey_subject = "???"
            try:
                survey_timeout = int(survey_params[2])
            except (TypeError, IndexError):
                survey_timeout = 90
            survey_options = survey_params[3:]
            stringed_opts = ", ".join(map(str, survey_options))
            survey_on = True
            await ctx.channel.send(
                f"/me - anket başladı ey sahip! · konu: {survey_subject} · süre: {survey_timeout} sn · seçenekler: {stringed_opts}")
            survey_option_counter: int = 0
            while survey_option_counter < len(survey_options):
                survey_votes.append([])
                survey_option_counter += 1
        survey_countdown_multiplier = 0
        while survey_on:
            survey_time_left = survey_timeout - survey_countdown_multiplier
            await asyncio.sleep(1)
            survey_countdown_multiplier += 1
            if survey_time_left == 0 or survey_time_left < 0:
                await ctx.channel.send("/me - anket sona erdi!")
                survey_votes_counter: int = 0
                survey_result = ""
                while survey_votes_counter < len(survey_options):
                    survey_result += str(survey_options[survey_votes_counter]) + ": " + str(find_rec_len_survey_opt(survey_votes_counter)) + " oy, "
                    survey_votes_counter += 1
                survey_on = False
                await ctx.channel.send(f"/me - anket sonuçları: {survey_result}")
            elif (survey_time_left % 30 == 0 or survey_time_left == 10 or (
                    6 > survey_time_left > 0)) and survey_time_left < survey_timeout:
                await ctx.channel.send(f"/me - anketin sona ermesine {survey_time_left} sn kaldı!")

    async def dump_songreq_list():
        global songreq_list
        songreq: int = 0
        songreq_dump = ""
        if len(songreq_list) > 0:
            while songreq < len(songreq_list):
                await tryFetchSpotiToken()
                spoti_track_by_uri = spoti.track(songreq_list[songreq])
                song_artist: int = 0
                song_artists = ""
                while song_artist < len(spoti_track_by_uri["artists"]):
                    song_artists += str(spoti_track_by_uri["artists"][song_artist]["name"])
                    if song_artist < (len(spoti_track_by_uri["artists"]) - 1):
                        song_artists += " & "
                    song_artist += 1
                song_title = str(spoti_track_by_uri["name"])
                songreq_dump += f"SingsNote {str(int(songreq) + 1)} · {str(song_artists)} - {str(song_title)} "
                songreq += 1
            if len(songreq_dump) <= 470:
                await ctx.channel.send(f"/me - şarkı istekleri: {songreq_dump.strip()}")
            else:
                songreq_longdump = ""
                songreq_longdump_list = songreq_dump.split("SingsNote")
                songreq_longdump_list = [x.strip() for x in songreq_longdump_list]
                del songreq_longdump_list[0]
                songreq_longdump_itemcount: int = 0
                songreq_longdump_charcount: int = 0
                while songreq_longdump_itemcount < len(songreq_longdump_list):
                    if (songreq_longdump_charcount <= 470) and (len(str(songreq_longdump_list[songreq_longdump_itemcount])) + len(str(songreq_longdump)) <= 470):
                        songreq_longdump += f" SingsNote {str(songreq_longdump_itemcount + 1)} · {str(songreq_longdump_list[songreq_longdump_itemcount])} "
                        songreq_longdump_charcount = len(songreq_longdump)
                        songreq_longdump_itemcount += 1
                        if songreq_longdump_itemcount == len(songreq_longdump_list):
                            await ctx.channel.send(f"/me - şarkı istekleri: {songreq_longdump.strip()}")
                    else:
                        await ctx.channel.send(f"/me - şarkı istekleri: {songreq_longdump.strip()}")
                        await asyncio.sleep(1)
                        songreq_longdump = ""
                        songreq_longdump_charcount = int(0)
        else:
            await ctx.channel.send(f"/me - şarkı isteği yok ki.")

    async def songreQu(songreq_params, song_requester):
        global songreq_on, songreq_list
        if songreq_on:
            if len(songreq_params) == 2:
                if re.match(r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*track[/:]*[A-Za-z0-9?=]+", songreq_params[1]):
                    if songreq_params[1] not in songreq_list:
                        await tryFetchSpotiToken()
                        req_song_get_data = spoti.track(songreq_params[1])
                        try:
                            songreq_list.append(req_song_get_data["uri"])
                            await ctx.channel.send(f"/me - şarkı isteğin kaydedildi @{song_requester}.")
                        except:
                            await ctx.channel.send(f"/me - var olmayan veya şu an çalınması mümkün olmayan bir şarkı seçtin @{song_requester}. ya da çok garip şeyler oluyor.")
            else:
                await ctx.channel.send(f"/me - komutu yanlış kullandın sanırım. kullanım örneği: !songReq spotify:track:3WHGMx4tWMsJdhHEVmG4ox veya !songReq https://open.spotify.com/track/3WHGMx4tWMsJdhHEVmG4ox @{song_requester}.")

    async def chooseModeSpotiQu():
        pause_songreq_list()
        await ctx.channel.send(f"/me - şarkı isteklerini artık toplamıyorum, sahip aralarından !srConfirm *args[int] komutuyla seçmek üzere.")
        await asyncio.sleep(1)
        await dump_songreq_list()

    async def confirmModeSpotiQu(confirmed_songreq_input):
        global songreq_list, confirmed_songreq_list, sr_opt_break, try_sl_exist
        await tryFetchSpotiToken()
        if not songreq_on:
            del confirmed_songreq_input[0]
            confirmed_songreq_list = confirmed_songreq_input
            amount_added_to_qu: int = 0
            for i in range(0, len(confirmed_songreq_input)):
                try:
                    confirmed_songreq = confirmed_songreq_input[i]
                    sr_opt_break = False
                except:
                    await ctx.channel.send(f"/me - onaylama işlemi sırasında feci bir hata ile karşılaştım ey sahip! onaylama işlemini durdurup şarkı isteklerini toplamaya devam ediyorum ben bari.")
                    resume_songreq_list()
                    sr_opt_break = True
                else:
                    try:
                        try_sl_exist = songreq_list[(int(confirmed_songreq) - 1)]
                        sr_opt_break = False
                    except IndexError:
                        await ctx.channel.send(f"/me - seçerken numaraları yanlış girmiş olma ihtimalin SnoopDogg kadar yüksek, ey sahip. bir daha deneyiver bari.")
                        resume_songreq_list()
                        sr_opt_break = True
                    else:
                        try:
                            spoti.add_to_queue(songreq_list[(int(confirmed_songreq) - 1)], "7c40c6a2973074584569fbce97ff5c99716dffae")
                            sr_opt_break = False
                            amount_added_to_qu += 1
                        except:
                            await ctx.channel.send(f"/me - spotify beni neden yoruyorsun ki aq?.. şarkılar sıraya eklenemedi, şarkı isteklerini toplamaya devam edeyim bari.")
                            resume_songreq_list()
                            sr_opt_break = True
                await asyncio.sleep(1)
            if not sr_opt_break:
                if len(confirmed_songreq_list) == amount_added_to_qu:
                    await ctx.channel.send(f"/me - onaylanan şarkılar sıraya eklendi!")
                else:
                    await ctx.channel.send(f"/me - onaylanan şarkılardan bazıları sıraya eklendi, bazıları öyle takılıyor bir yerlerde, bir şeyler oldu, ben de pek anlamadım.")
                reset_songreq_list()
                reset_confirmed_songreq_list()
                resume_songreq_list()
        else:
            await ctx.channel.send(f"/me - şarkı isteklerini onaylamak için önce !srChoose komutunu kullanıp, istekleri görüntülemek daha mantıklı değil mi sahip?")

    async def currentSong():
        await tryFetchSpotiToken()
        get_current_song = spoti.current_user_playing_track()
        c_song_artist = 0
        c_song_artists = ""
        while c_song_artist < len(get_current_song["item"]["artists"]):
            c_song_artists += str(get_current_song["item"]["artists"][c_song_artist]["name"])
            if c_song_artist < (len(get_current_song["item"]["artists"]) - 1):
                c_song_artists += " & "
            c_song_artist += 1
        c_song_title = str(get_current_song["item"]["name"])
        await ctx.channel.send(f"/me - şu an çalan şarkı: \"{str(c_song_artists)} - {str(c_song_title)}\"")

    async def getFollowage(followage_command, followage_issuer):
        if len(followage_command) == 1:
            followage_user = followage_issuer
        else:
            followage_user = followage_command[1]
        ht_followage_req = requests.get(f"https://api.2g.be/twitch/followage/sheptang/{followage_user}?format=mwdhms", allow_redirects=False)
        ht_followage_resp = str(ht_followage_req.text)
        try:
            followage_data = str(ht_followage_resp.split(" for ")[1])
        except IndexError:
            if followage_user == "sheptang":
                await ctx.channel.send(f"/me - komikmiş @{followage_issuer}.")
            else:
                await ctx.channel.send(f"/me - @{followage_user} bizi takip etmiyor.")
        else:
            followage_data = await replaceTimeString(followage_data)
            await ctx.channel.send(f"/me - @{followage_user} şu kadardır takipte: {followage_data}")

    async def getUptime():
        ht_uptime_req = requests.get("https://decapi.me/twitch/uptime/sheptang", allow_redirects=False)
        ht_uptime_resp = str(ht_uptime_req.text)
        uptime_data = await replaceTimeString(ht_uptime_resp)
        if find_whole_word("offline", uptime_data):
            await ctx.channel.send(f"/me - yayın kapalı :)")
        else:
            await ctx.channel.send(f"/me - yayın şu kadardır açık: {uptime_data}")

    if find_whole_word("sa", message_content.lower()) or find_whole_word("slm", message_content.lower()) or find_whole_word("selam", message_content.lower()) or find_whole_word("selamün aleyküm", message_content.lower()) or find_whole_word("selamun aleykum", message_content.lower()):
        await ctx.channel.send(f"/me - as @{ctx.author.name}!")

    if possible_command == "!beeptang":
        await ctx.channel.send("/me - komutlar ve kullanım: sheptang.com/t/beeptang")
    elif possible_command == "!gapanic" and (possible_command_issuer in mod_username_list):
        reset_giveaway_list()
        await ctx.channel.send("/me - panik butonuyla çekiliş sıfırlandı ey sahip!")
    elif possible_command == "?gaannounce" and (possible_command_issuer in mod_username_list):
        await ctx.channel.send("/me - !gaAnnounce *çekiliş[str] *süre[sec] *adet[int]")
    elif possible_command == "!gaannounce" and (possible_command_issuer in mod_username_list):
        await ctx.channel.send("/me - @sheptang, çekiliş 10 saniye sonra başlayacak ey sahip!")
        await ctx.channel.send("/me - çekilişe \"!çekiliş\" veya \"!cekilis\" komutlarından biriyle katılabilirsin.")
        giveaway_on = False
        await asyncio.sleep(10)
        await gaEngine(message_content.split())
    elif possible_command == "?gastart" and (possible_command_issuer in mod_username_list):
        await ctx.channel.send("/me - !gaStart *çekiliş[str] *süre[sec] *adet[int] tekrarlı[bool] sonuçlar[bool]")
    elif possible_command == "!gastart" and (possible_command_issuer in mod_username_list):
        await gaEngine(message_content.split())
    elif possible_command == "!svpanic" and (possible_command_issuer in mod_username_list):
        reset_survey_list()
    elif possible_command == "?svannounce" and (possible_command_issuer in mod_username_list):
        await ctx.channel.send("/me - !svAnnounce *konu[str] *süre[sec] *args[]")
    elif possible_command == "!svannounce" and (possible_command_issuer in mod_username_list):
        if len(message_content.split()) > 3:
            await ctx.channel.send("/me - @sheptang, anket 10 saniye sonra başlayacak ey sahip!")
            await ctx.channel.send("/me - oy kullanmak için \"!oy\" komutunu kullanabilirsin. örneğin 3. seçeneğe oy vermek için: \"!oy 3\". anket süresince en son kullandığın geçerli oy geçerlidir ve geçersiz oylar otomatik olarak silinir.")
            survey_on = False
            await asyncio.sleep(10)
            await svEngine(message_content.split())
        else:
            await ctx.channel.send("/me - !svAnnounce *konu[str] *süre[sec] *args[]")
    elif possible_command == "?svstart" and (possible_command_issuer in mod_username_list):
        await ctx.channel.send("/me - !svStart *konu[str] *süre[sec] *args[]")
    elif possible_command == "!svstart" and (possible_command_issuer in mod_username_list):
        await svEngine(message_content.split())
    elif possible_command == "?songreq":
        await ctx.channel.send("/me - !songReq *spotifyŞarkıUri[str]")
    elif possible_command == "!songreq":
        await songreQu(message_content.split(), str(possible_command_issuer))
    elif possible_command == "!srpause" and (possible_command_issuer in mod_username_list):
        pause_songreq_list()
    elif possible_command == "!srresume" and (possible_command_issuer in mod_username_list):
        resume_songreq_list()
    elif possible_command == "!srdump" and possible_command_issuer == "sheptang":
        await dump_songreq_list()
    elif possible_command == "!srchoose" and (possible_command_issuer in mod_username_list):
        await chooseModeSpotiQu()
    elif possible_command == "?srconfirm" and possible_command_issuer == "sheptang":
        await ctx.channel.send("/me - !srConfirm *args[int]")
    elif possible_command == "!srconfirm" and possible_command_issuer == "sheptang":
        await confirmModeSpotiQu(message_content.split())
    elif possible_command == "!şarkı" or possible_command == "!müzik":
        await currentSong()
    elif possible_command == "!followage" or possible_command == "!takip":
        await getFollowage(message_content.split(), str(possible_command_issuer))
    elif possible_command == "!uptime" or possible_command == "!yayın":
        await getUptime()
    elif possible_command == "!sub" or possible_command == "!abone":
        await ctx.channel.send("/me - https://subs.twitch.tv/sheptang linkinden veya !prime komutuyla Prime abonesi olabilirsin!")
    elif possible_command == "!bağış" or possible_command == "!donate":
        await ctx.channel.send(f"/me - https://streamlabs.com/sheptang veya https://www.bynogame.com/sheptang adresinden bağış yapabilirsin, @{str(possible_command_issuer)}.")
    elif possible_command == "!dc" or possible_command == "!discord":
        await ctx.channel.send("/me - https://discord.gg/8U5Cxt9 adresinden Discord kanalına katılabilirsin!")
    elif possible_command == "!diziler":
        await ctx.channel.send("/me - İzlediğim dizileri şuradan görebilirsin: https://www.tvtime.com/en/user/8893125/profile.")
    elif possible_command == "!ig" or possible_command == "!instagram":
        await ctx.channel.send("/me - Instagram: https://www.instagram.com/sheptang")
    elif possible_command == "!playlist" or possible_command == "!spotify":
        await ctx.channel.send("/me - Spotify çalma listelerim şurada: https://open.spotify.com/user/sheptang")
    elif possible_command == "!prime":
        await ctx.channel.send("/me - https://www.twitch.tv/prime linkini kullanarak Prime'a katılabilirsin.")
    elif possible_command == "!sosyal" or possible_command == "!social":
        await ctx.channel.send("/me - Instagram'dan: https://www.instagram.com/sheptang ve Twitter'dan: https://www.twitter.com/sheptang beni takip edebilirsin!")
    elif possible_command == "!steam":
        await ctx.channel.send("/me - Steam hesabım: https://steamcommunity.com/id/sheptang/")
    elif possible_command == "!twitter":
        await ctx.channel.send("/me - Twitter: https://www.twitter.com/sheptang")
    elif possible_command == "!csCross":
        await ctx.channel.send("/me - CS:GO Cross: CSGO-6YyYu-HPRwp-jA4fi-NMrsu-WaMbM")
    elif possible_command == "!çekiliş" or possible_command == "!cekilis":
        if giveaway_on:
            if possible_command_issuer not in giveaway_list:
                giveaway_list.append(possible_command_issuer)
    elif possible_command == "!oy" and survey_on:
        casted_vote = message_content.split()[1]
        if casted_vote.isdigit():
            if int(casted_vote) > 0:
                if int(casted_vote) <= len(survey_options):
                    sv_opt_break = False
                    survey_option_vote_counter: int = 0
                    while (survey_option_vote_counter < len(survey_options)) and (not sv_opt_break):
                        if possible_command_issuer not in survey_votes[survey_option_vote_counter]:
                            sv_opt_break = False
                        else:
                            survey_votes[survey_option_vote_counter].remove(possible_command_issuer)
                            sv_opt_break = True
                        survey_option_vote_counter += 1
                    try:
                        try_sv_exist = survey_votes[int(casted_vote) - 1]
                        vote_error = False
                    except IndexError:
                        vote_error = True
                    if not vote_error:
                        survey_votes[int(casted_vote) - 1].append(possible_command_issuer)


if __name__ == "__main__":
    beeptang.run()
