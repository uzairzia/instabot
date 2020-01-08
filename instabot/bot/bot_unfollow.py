from tqdm import tqdm
import time
from datetime import datetime

def unfollow(self, user_id):
    if not self.reached_limit("unfollows"):
        if self.blocked_actions["unfollows"]:
            self.logger.warning("YOUR `UNFOLLOW` ACTION IS BLOCKED")
            if self.blocked_actions_protection:
                self.logger.warning(
                    "blocked_actions_protection ACTIVE. " "Skipping `unfollow` action."
                )
                return False

        user_id = self.convert_to_user_id(user_id)
        user_info = self.get_user_info(user_id)

        if not user_info:
            self.logger.info("Can't get user_id=%s info" % str(user_id))
            return False  # No user_info

        username = user_info.get("username")

        if self.log_follow_unfollow:
            msg = "Going to unfollow `user_id` {} with username {}.".format(
                user_id, username
            )
            self.logger.info(msg)
        else:
            self.console_print(
                "===> Going to unfollow `user_id`: {} with username: {}".format(
                    user_id, username
                )
            )

        if self.check_user(user_id, unfollowing=True):
            return True  # whitelisted user

        _r = self.api.unfollow(user_id)
        if _r == "feedback_required":
            self.logger.error("`Unfollow` action has been BLOCKED...!!!")
            if not self.blocked_actions_sleep:
                if self.blocked_actions_protection:
                    self.logger.warning(
                        "Activating blocked actions \
                        protection for `Unfollow` action."
                    )
                    self.blocked_actions["unfollows"] = True
            else:
                if (
                    self.sleeping_actions["unfollows"]
                    and self.blocked_actions_protection
                ):
                    self.logger.warning(
                        "This is the second blocked \
                        `Unfollow` action."
                    )
                    self.logger.warning(
                        "Activating blocked actions \
                        protection for `Unfollow` action."
                    )
                    self.sleeping_actions["unfollows"] = False
                    self.blocked_actions["unfollows"] = True
                else:
                    self.logger.info(
                        "`Unfollow` action is going to sleep \
                        for %s seconds."
                        % self.blocked_actions_sleep_delay
                    )
                    self.sleeping_actions["unfollows"] = True
                    self.delay(duration=self.blocked_actions_sleep_delay)
            return False
        if _r:
            if self.log_follow_unfollow:
                msg = "Unfollowed `user_id` {} with username {}".format(
                    user_id, username
                )
                self.logger.info(msg)
            else:
                msg = "===> Unfollowed, `user_id`: {}, user_name: {}"
                self.console_print(msg.format(user_id, username), "yellow")
            self.unfollowed_file.append(user_id)
            self.total["unfollows"] += 1
            if user_id in self.following:
                self.following.remove(user_id)
            if self.blocked_actions_sleep and self.sleeping_actions["unfollows"]:
                self.logger.info("`Unfollow` action is no longer sleeping.")
                self.sleeping_actions["unfollows"] = False
            return True
    else:
        self.logger.info("Out of unfollows for today.")
    return False


def unfollow_users(self, user_ids):
    broken_items = []
    self.logger.info("Going to unfollow {} users.".format(len(user_ids)))
    user_ids = set(map(str, user_ids))
    filtered_user_ids = list(set(user_ids) - set(self.whitelist))
    if len(filtered_user_ids) != len(user_ids):
        self.logger.info(
            "After filtration by whitelist {} users left.".format(
                len(filtered_user_ids)
            )
        )

    self.logger.info("Script will auto-pause after unfollowing each user. (without outputting delay)\n"
    "\t\t\t\t\t...Delay Range:\n" 
    "\t\t\t\t\t\t..if unfollowing successful: {} seconds\n"
    "\t\t\t\t\t\t..if unfollowing unsuccessful: {} seconds\n".format(self.delays['unfollow'],self.delays['error']))


    previous_unfollow_result = None

    for user_id in tqdm(filtered_user_ids, desc="Processed users"):
        if previous_unfollow_result == True: 
            self.delay("unfollow",output=0)
        elif previous_unfollow_result == False:
            self.delay("error",output=0)
        else:
            pass
        
        print("\n")

        if not self.unfollow(user_id):
            previous_unfollow_result = False

            i = filtered_user_ids.index(user_id)
            broken_items = filtered_user_ids[i:]
            break
        else:
            previous_follow_result = True
    print("\n")

    self.logger.info("DONE: Total unfollowed {} users.".format(self.total["unfollows"]))
    return broken_items


def unfollow_non_followers(self, days_followed_ago, n_to_unfollows=None):
    self.logger.info("Unfollowing non-followers who were followed %d days ago or more." %(days_followed_ago))

    print()

    non_followers = set(self.following) - set(self.followers) - self.friends_file.set
    non_followers = list(non_followers)
    
    # Get current date
    now = datetime.now()

    # Get content from followed date file
    followed_users_date_string = self.read_file("followed_date.txt")

    # Split multiple lines, each line contains userID and datetime split by comma
    followed_users_date_strings_array = followed_users_date_string.split('\n')

    # Remove any empty elements from above strings array
    followed_users_date_strings_array = list(filter(None, followed_users_date_strings_array))

    temp_non_followers = []
    if len(followed_users_date_strings_array) != 0:
        # Split each line using comma as delimiter
        followed_users_date_array = [line.strip().split(',') for line in followed_users_date_strings_array]

        followed_users_array = [item[0] for item in followed_users_date_array]
        followed_date_array = [item[1] for item in followed_users_date_array]

        # Remove elements from the non_followers list who were followed in the last `days_followed_ago` days
        for non_follower in non_followers:
            if non_follower in followed_users_array:
                non_follower_index = followed_users_array.index(non_follower)
                non_follower_date_string = followed_date_array[non_follower_index]
                
                # Create a datetime object using above string
                non_follower_datetime = datetime.strptime(non_follower_date_string, '%Y-%m-%d %H:%M:%S.%f')

                if ((now - non_follower_datetime).days >= days_followed_ago):
                    temp_non_followers.append(non_follower)
        
    non_followers = temp_non_followers

    if (len(non_followers) != 0):
        if (n_to_unfollows is not None):
            n_to_unfollows = min(n_to_unfollows, len(non_followers))
            self.logger.info("Going to unfollow %d user(s)." %(n_to_unfollows))
        else:
            self.logger.info("Going to unfollow %d user(s)." %(len(non_followers)))
        print()

        self.logger.info("Script will auto-pause after unfollowing each user. (without outputting delay)\n"
                         "\t\t\t\t\t...Delay Range:\n"
                         "\t\t\t\t\t\t..if unfollowing successful: {} seconds\n"
                         "\t\t\t\t\t\t..if unfollowing unsuccessful: {} seconds\n".format(self.delays['unfollow'],
                                                                                          self.delays['error']))

        for user_id in tqdm(non_followers[:n_to_unfollows]):
            if self.reached_limit("unfollows"):
                self.logger.info("Out of unfollows for today.")
                return
            print("\n")
            result = self.unfollow(user_id)

        print()
        self.logger.info("DONE: Unfollowed {} users today (until now).".format(self.total["unfollows"]))        
    else:
        self.logger.info("No users to unfollow.")


def unfollow_everyone(self):
    self.unfollow_users(self.following)
