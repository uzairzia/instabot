import os
from mimetypes import guess_type

from tqdm import tqdm

WELCOMED_FOLLOWERS_FILE = "welcomed_followers.txt"

def send_message(self, text, user_ids, thread_id=None):
    """
    :param self: bot
    :param text: text of message
    :param user_ids: list of user_ids for creating group or
    one user_id for send to one person
    :param thread_id: thread_id
    """
    if self.reached_limit("messages"):
        self.logger.info("Out of messages for today.")
        return False

    user_ids = _get_user_ids(self, user_ids)
    if not isinstance(text, str) and isinstance(user_ids, (list, str)):
        self.logger.error("Text must be an string, user_ids must be an list or string")
        return False

    if len(user_ids) == 1:
        user_ids = user_ids[:1]

    urls = self.extract_urls(text)
    item_type = "link" if urls else "text"
    if self.api.send_direct_item(
        item_type, user_ids, text=text, thread=thread_id, urls=urls
    ) == True:
        self.total["messages"] += 1
        self.logger.info("Message to {user_ids} successfully sent".format(user_ids=user_ids))
        return True
    else:
        self.logger.info("Message to {user_ids} wasn't sent".format(user_ids=user_ids))
        return False


def send_messages(self, text, user_ids, amount):
    broken_items = []
    if not user_ids:
        self.logger.info("User must be at least one.")
        return broken_items
    amount = min(amount, len(user_ids))
    user_ids = user_ids[:amount]
    self.logger.info("Going to send %d messages." % (amount))

    self.logger.info("Script will auto-pause after sending message to each user. (without outputting delay)\n"
                     "\t\t\t\t\t...Delay Range:\n"
                     "\t\t\t\t\t\t..if messaging successful: {} seconds\n"
                     "\t\t\t\t\t\t..if messaging unsuccessful: {} seconds\n".format(self.delays['message'],
                                                                                    self.delays['error']))

    previous_message_result = None
    for user in tqdm(user_ids):
        if previous_message_result == True:
            self.delay("message", output=0)
        elif previous_message_result == False:
            self.delay("error", output=0)
        else:
            pass

        print("\n")

        if not self.send_message(text, user):
            self.error_delay()
            broken_items = user_ids[user_ids.index(user) :]
            previous_message_result = False
            break
        else:
            previous_message_result = True

        self.delay("message", output=0)

    self.logger.info(
        "DONE: Messaged {} users today (until now).".format(self.total["messages"])
    )

    return broken_items

def send_message_new_followers(self, text, amount=None):
    followers = self.followers
    if not followers:
        self.logger.info("You don't have any followers.")
        return

    messaged_followers_string = self.read_file(WELCOMED_FOLLOWERS_FILE)
    messaged_followers_array = list(filter(None, messaged_followers_string.strip().split("\n")))

    inbox_users = []
    if self.api.get_inbox_v2():
        inbox = self.last_json["inbox"]["threads"]
        for conversation in inbox:
            user_ids = conversation["users"]
            for user in user_ids:
                inbox_users.append(user["pk"])

    new_followers = list(set(followers) - set(messaged_followers_array) - set(inbox_users))
    if not new_followers:
        self.logger.info("No new followers who have not been messaged.")
        return
    else:
        new_followers = set(new_followers[:amount] if amount else new_followers)

    new_followers_messaged = []
    broken_items = []

    self.logger.info("Going to send %d messages." % (len(new_followers)))

    self.logger.info("Script will auto-pause after sending message to each user. (without outputting delay)\n"
                     "\t\t\t\t\t...Delay Range:\n"
                     "\t\t\t\t\t\t..if messaging successful: {} seconds\n"
                     "\t\t\t\t\t\t..if messaging unsuccessful: {} seconds\n".format(self.delays['message'],
                                                                                    self.delays['error']))

    previous_message_result = None
    for follower in tqdm(new_followers):
        if previous_message_result == True:
            self.delay("message", output=0)
        elif previous_message_result == False:
            self.delay("error", output=0)
        else:
            pass

        print("\n")

        if self.send_message(text, follower):
            new_followers_messaged.append(follower)
            self.write_file(WELCOMED_FOLLOWERS_FILE, str(follower) + "\n")
            previous_message_result = True
        else:
            broken_items.append(follower)
            previous_message_result = False

    print("\n")
    self.logger.info(
        "DONE: Messaged {} users today (until now).".format(self.total["messages"])
    )

    return broken_items

    # if not bot.check_if_file_exists(WELCOMED_FOLLOWERS_FILE):
    #     followers = bot.get_user_followers(bot.user_id)
    #     followers = map(str, followers)
    #     followers_string = '\n'.join(followers)
    #     with open(WELCOMED_FOLLOWERS_FILE, 'w') as users_file:
    #         users_file.write(followers_string)
    #     print(
    #         'All followers saved in file {users_path}.\n'
    #         'In a next time, for all new followers script will send messages.'.format(
    #             users_path=WELCOMED_FOLLOWERS_FILE
    #         )
    #     )
    #     exit(0)

    # notified_users = bot.read_list_from_file(WELCOMED_FOLLOWERS_FILE)
    # print('Read saved list of notified users. Count: {count}'.format(
    #     count=len(notified_users)
    # ))
    # all_followers = bot.get_user_followers(bot.user_id)
    # print('Amount of all followers is {count}'.format(
    #     count=len(all_followers)
    # ))


    # if not new_followers:
    #     print('New followers not found')
    #     exit()

    # print('Found new followers. Count: {count}'.format(
    #     count=len(new_followers)
    # ))

    # new_notified_users = []

    # for follower in tqdm(new_followers):
    #     if bot.send_message("Sorry for the disturbance.", follower):
    #         new_notified_users.append(follower)
    #         print("done")
    #     else:
    #         print("failed")
    #     print("sleeping")
    #     time.sleep(30)


def send_media(self, media_id, user_ids, text="", thread_id=None):
    """
    :param media_id:
    :param self: bot
    :param text: text of message
    :param user_ids: list of user_ids for creating group or one user_id
    for send to one person
    :param thread_id: thread_id
    """
    user_ids = _get_user_ids(self, user_ids)
    if not isinstance(text, str) and not isinstance(user_ids, (list, str)):
        self.logger.error("Text must be an string, user_ids must be an list or string")
        return False
    if self.reached_limit("messages"):
        self.logger.info("Out of messages for today.")
        return False

    media = self.get_media_info(media_id)
    media = media[0] if isinstance(media, list) else media

    self.delay("message")
    if self.api.send_direct_item(
        "media_share",
        user_ids,
        text=text,
        thread=thread_id,
        media_type=media.get("media_type"),
        media_id=media.get("id"),
    ):
        self.total["messages"] += 1
        return True

    self.logger.info("Message to {user_ids} wasn't sent".format(user_ids=user_ids))
    return False


def send_medias(self, media_id, user_ids, text):
    broken_items = []
    if not user_ids:
        self.logger.info("User must be at least one.")
        return broken_items
    self.logger.info("Going to send %d messages." % (len(user_ids)))
    for user in tqdm(user_ids):
        if not self.send_media(media_id, user, text):
            self.error_delay()
            broken_items = user_ids[user_ids.index(user) :]
            break
    return broken_items


def send_hashtag(self, hashtag, user_ids, text="", thread_id=None):
    """
    :param hashtag: hashtag
    :param self: bot
    :param text: text of message
    :param user_ids: list of user_ids for creating group or one
    user_id for send to one person
    :param thread_id: thread_id
    """
    user_ids = _get_user_ids(self, user_ids)
    if not isinstance(text, str) and not isinstance(user_ids, (list, str)):
        self.logger.error("Text must be an string, user_ids must be an list or string")
        return False

    if self.reached_limit("messages"):
        self.logger.info("Out of messages for today.")
        return False

    self.delay("message")
    if self.api.send_direct_item(
        "hashtag", user_ids, text=text, thread=thread_id, hashtag=hashtag
    ):
        self.total["messages"] += 1
        return True

    self.logger.info("Message to {user_ids} wasn't sent".format(user_ids=user_ids))
    return False


def send_profile(self, profile_user_id, user_ids, text="", thread_id=None):
    """
    :param profile_user_id: profile_id
    :param self: bot
    :param text: text of message
    :param user_ids: list of user_ids for creating group or
    one user_id for send to one person
    :param thread_id: thread_id
    """
    profile_id = self.convert_to_user_id(profile_user_id)
    user_ids = _get_user_ids(self, user_ids)
    if not isinstance(text, str) and not isinstance(user_ids, (list, str)):
        self.logger.error("Text must be an string, user_ids must be an list or string")
        return False

    if self.reached_limit("messages"):
        self.logger.info("Out of messages for today.")
        return False

    self.delay("message")
    if self.api.send_direct_item(
        "profile", user_ids, text=text, thread=thread_id, profile_user_id=profile_id
    ):
        self.total["messages"] += 1
        return True
    self.logger.info("Message to {user_ids} wasn't sent".format(user_ids=user_ids))
    return False


def send_like(self, user_ids, thread_id=None):
    """
    :param self: bot
    :param user_ids: list of user_ids for creating group or
    one user_id for send to one person
    :param thread_id: thread_id
    """
    user_ids = _get_user_ids(self, user_ids)
    if not isinstance(user_ids, (list, str)):
        self.logger.error("Text must be an string, user_ids must be an list or string")
        return False

    if self.reached_limit("messages"):
        self.logger.info("Out of messages for today.")
        return False

    self.delay("message")
    if self.api.send_direct_item("like", user_ids, thread=thread_id):
        self.total["messages"] += 1
        return True
    self.logger.info("Message to {user_ids} wasn't sent".format(user_ids=user_ids))
    return False


def send_photo(self, user_ids, filepath, thread_id=None):
    """
    :param self: bot
    :param filepath: file path to send
    :param user_ids: list of user_ids for creating group or
    one user_id for send to one person
    :param thread_id: thread_id
    """
    user_ids = _get_user_ids(self, user_ids)
    if not isinstance(user_ids, (list, str)):
        self.logger.error("user_ids must be a list or string")
        return False

    if self.reached_limit("messages"):
        self.logger.info("Out of messages for today.")
        return False

    if not os.path.exists(filepath):
        self.logger.error("File %s is not found", filepath)
        return False

    mime_type = guess_type(filepath)
    if mime_type[0] != "image/jpeg":
        self.logger.error("Only jpeg files are supported")
        return False

    self.delay("message")
    if not self.api.send_direct_item(
        "photo", user_ids, filepath=filepath, thread=thread_id
    ):
        self.logger.info("Message to %s wasn't sent", user_ids)
        return False

    self.total["messages"] += 1
    return True


def _get_user_ids(self, user_ids):
    if isinstance(user_ids, str):
        user_ids = self.convert_to_user_id(user_ids)
        return [user_ids]
    return [self.convert_to_user_id(user) for user in user_ids]


def approve_pending_thread_requests(self):
    pending = self.get_pending_thread_requests()
    if pending:
        for thread in pending:
            thread_id = thread["thread_id"]
            self.api.approve_pending_thread(thread_id)
            if self.api.last_response.status_code == 200:
                self.logger.info("Approved thread: {}".format(thread_id))
            else:
                self.logger.error("Could not approve thread {}".format(thread_id))
