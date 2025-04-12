import os
import json
import time
import discord
import re
from random import choice

from modules.logger import AsyncLogger

log = AsyncLogger()


class Chat:
    def get_thinking_messages(self, username) -> tuple[str, str]:
        phrase_opening = [
            "hmm",
            "hi",
            "hello",
            "hey",
            "one sec",
            "wait right there",
            "yo",
            "howdy",
            "oh, hey there",
            "well, well, well",
            "uh-huh",
            "why, hello",
            "why hello there",
            "hello there",
            "hey, what's up",
            "excuse me",
            "hey, you there",
            "how's it going",
            "ahoy",
            "yoohoo",
            "oh hey, you",
            "wait one sec",
        ]
        thinking_phrases = [
            "let me process this information and come up with a helpful response",
            "let me mull this over and come up with a helpful response for you",
            "let me ponder this for a moment and come up with something helpful for you",
            "let me put on my thinking cap and sort this out for you",
            "let me chew on this for a bit and come back with a solid response",
            "let me marinate on this info and cook up a helpful reply for you",
            "let me let this simmer in my mind and whip up a useful response for you",
            "let me percolate on this and serve up a tasty solution",
            "let me stew on this and dish out a relevant reply",
            "let me ponder this and whip up a valuable response for you",
            "let me brew on this and craft a helpful reply",
            "let me ponder this and serve up a meaningful response",
            "let me contemplate this and provide you with a useful response",
            "let me think this over and offer you some valuable insights",
            "let me roll this around in my head and present you with a well-thought-out response",
            "let me let this marinate in my thoughts and deliver a helpful solution for you",
            "let me mull over this information and come up with a beneficial response for you",
            "let me ruminate on this and provide you with a constructive reply",
            "let me let this sink in and offer you some insightful advice",
            "let me reflect on this and give you a thoughtful response",
            "let me ponder deeply and offer you a well-reasoned answer",
            "let me delve into this and give you a comprehensive response",
            "let me analyze this and give you a detailed solution",
        ]
        continue_phrases = [
            "let me continue the conversation and dive deeper into this topic",
            "let me progress and explore this idea further",
            "let me continue down this path and see where it leads us",
            "let me build on that and expand our discussion",
            "let me delve deeper and uncover more insights",
            "let me carry on and unravel the next chapter of our chat",
            "let me move forward and delve deeper into this topic",
            "let me continue our journey through this discussion",
            "let me advance and uncover even more interesting points",
            "let me maintain the momentum and explore new angles",
            "let me navigate through this thought and shed light on new perspectives",
            "let me keep the dialogue going and delve into intricate details",
            "let me steer the conversation towards deeper insights and meaningful connections",
            "let me press on and delve deeper into the intricacies of this topic",
            "let me forge ahead and uncover the hidden gems within this discussion",
            "let me dive into the depths of this topic and unearth valuable insights",
            "let me proceed with exploring this concept further and expanding our understanding",
            "let me push forward and illuminate new facets of this conversation",
            "let me advance our discourse and uncover layers of knowledge",
            "let me propel the discussion forward and dissect key elements",
            "let me delve into different perspectives and broaden our horizons",
            "let me explore uncharted territories within this subject",
            "let me delve deeper into the nuances of this topic and draw connections",
            "let me venture into new realms of thought and expand our insights",
            "let me delve into the intricacies of this discussion and extract valuable information",
            "let me navigate through the complexities to unveil hidden truths",
            "let me push the boundaries of this conversation to reveal new perspectives",
            "let me unravel the layers of this topic to reveal its true depth",
            "let me journey further into this topic to discover undiscovered aspects",
            "let me forge ahead with our conversation to uncover fresh insights",
        ]

        return (
            f"{choice(phrase_opening)}, {username.lower()}, {choice(thinking_phrases)}",
            f"{choice(phrase_opening)}, {username.lower()}, {choice(continue_phrases)}",
        )

    async def process_response(
        self,
        stream_object,
        start_time: int,
        thread_name: str,
        message: discord.Message,
        continue_message: str,
        stream: bool = True,
        answer: discord.Message = None,
        claude: bool = False,
    ):
        part_chunks: list = []  # list of chunks in current message
        filtered_chunks: list[str] = []  # chunks without None values
        token: int = 0  # amount of tokens returned from api
        part_length: int = 0  # length of current message
        max_length: int = 1900  # max amount of characters allowed per reply
        output_chunks = []
        output = ""
        update_amount: float = 1
        queried_update: int = (
            update_amount  # time since update_time that will trigger stream update
        )

        for chunk in stream_object:
            token += 1

            if token == 1:
                update_time = (
                    time.time()
                )  # time at which streaming starts versus querying of ai

            chunk_time = time.time() - start_time
            part_chunks.append(chunk)

            chunk_message = chunk.choices[0].delta.content if not claude else chunk

            # chunk_message = chunk
            part_length += len(chunk_message) if chunk_message is not None else 0
            filtered_chunks.append(chunk_message)
            output_chunks.append(chunk_message)

            filtered_chunks = [m for m in filtered_chunks if m is not None]
            output_chunks = [m for m in output_chunks if m is not None]
            full_reply_content = "".join([m for m in filtered_chunks])
            output = "".join([m for m in output_chunks])

            if part_length >= max_length:
                await log.info(f"{thread_name}  Streaming message")
                await log.info(f"{thread_name}  Continuing streaming in new message")

                filtered_chunks = []
                part_length = 0

                if stream:
                    await answer.edit(content=f"{full_reply_content}...")
                    answer = await message.reply(
                        f"{continue_message} <a:typing:1206412960130408448>"
                    )
                else:
                    await message.reply(content=f"{full_reply_content}...")

                full_reply_content = ""
                queried_update += update_amount

            if (time.time() - update_time) > queried_update * update_amount:
                await log.info(f"{thread_name}  Streaming message")

                if stream and len(full_reply_content) > 0:
                    await answer.edit(
                        content=f"{full_reply_content} <a:typing:1206412960130408448>"
                    )

                queried_update += 1

        return {
            "filtered_chunks": filtered_chunks,
            "output": output,
            "chunk_time": chunk_time,
            "update_time": update_time,
            "answer": answer,
        }


class Thread:
    async def populate(
        self,
        channel: discord.TextChannel,
        creator: int,
        dm: bool = False,
        create: bool = False,
        greeting: str = None,
        bot_config: dict = {"memory": {"inv": True, "tcl": 30}},
        verbose: bool = False,
    ) -> None:
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        if dm:
            dm_id = channel.id
            guild_id = None
            channel_name = None
        else:
            dm_id = None
            guild_id = channel.guild.id
            channel_name = re.sub(r"[^a-zA-Z0-9-_]+", "", channel.name)
            channel_display = channel.name

        try:
            if not dm:
                path = os.path.join(current_dir, "threads", str(guild_id), channel_name)
            else:
                path = os.path.join(current_dir, "threads", "dm", str(dm_id))
            if not os.path.exists(path) and create:
                # create path
                name = ("#" + channel_display) if not dm else ("@" + str(dm_id))

                await log.info(
                    f'{name}  Creating folder ./threads/{"dm" if dm else str(guild_id)}/{channel_name if channel_name else str(dm_id)}'
                )
                os.makedirs(path)
                await log.success(f"{name}  Created folder")

                await log.info(
                    f"{name}  Populating folder with config and memory files"
                )
                with open(os.path.join(path, ".config.json"), "w") as f:
                    json.dump(
                        {
                            "bot": bot_config,
                            "thread": {
                                "name": f"{f'dm-{str(dm_id)}' if dm else channel_name}",
                                "creator": dm_id if dm else creator,
                                "date": int(round(time.time())),
                                "permissions": {
                                    "everyone": "chat",
                                    "invitees": "chat",
                                },
                            },
                        },
                        f,
                        indent=4,
                    )
                with open(os.path.join(path, "thread-specific-m.json"), "w") as f:
                    json.dump(
                        (
                            {"0": {"role": "user", "content": " "}}
                            if not greeting
                            else {
                                "0": {"role": "user", "content": " "},
                                "1": {"role": "assistant", "content": greeting},
                            }
                        ),
                        f,
                        indent=4,
                    )
                await log.success(f"{name}  Populated folder")
                if verbose and not dm:
                    await channel.send(f"`VERBOSE > Populated folder`")
                await log.success(f"{name}  Done!")

        except AttributeError:
            await log.warning(
                "'NoneType' object has no attribute 'id'; ephemeral message?"
            )
            return

    async def path(self, message: discord.Message, dm: bool = False) -> str | None:
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        try:
            if dm:
                return os.path.join(
                    current_dir, "threads", "dm", str(message.channel.id)
                )
            else:
                return os.path.join(
                    current_dir,
                    "threads",
                    str(message.guild.id),
                    re.sub(r"[^a-zA-Z0-9-_]+", "", message.channel.name),
                )
        except AttributeError:
            await log.error("AttributeError: could not find thread in on_message")
            return

    class TSM:

        def __init__(self, thread_path: str):
            self.thread_path = thread_path

        async def fetch(self):
            file = os.path.join(self.thread_path, "thread-specific-m.json")

            if os.path.exists(file):
                with open(file, "r") as f:
                    return json.load(f)
            else:
                return {}

        def roll(self, d: dict, max: int, new: any = None, smart: bool = False) -> dict:
            if max < 1:  # return nothing
                return {}
            if not d:  # if d doesn't exist
                return {"0": new}  # return new dictionary
            if len(d) > max:  # if d is longer than the expected length
                if (
                    list(d.values())[0]["role"] == "assistant"
                    or (list(d.values())[0]["role"] == "user" and len(d) > (max + 1))
                    or not smart
                ):
                    d = dict(
                        list(d.items())[-max:]
                    )  # trim d to only include the last items that result in an expected length
                else:
                    return d
            if new:
                d[str(int(list(d)[-1]) + 1)] = new  # insert the new item
            return d

        async def update(self, message: dict[str, str], window: int = 15):
            data = await self.fetch()
            data = self.roll(d=data, max=window, new=message)
            with open(
                os.path.join(self.thread_path, "thread-specific-m.json"), "w"
            ) as f:
                json.dump(data, f, indent=4)

        async def unpack(self):
            memory_file = os.path.join(self.thread_path, "thread-specific-m.json")

            if os.path.exists(memory_file):
                with open(memory_file, "r") as memf:
                    memory_data = json.load(memf)
            else:
                memory_data = {}

            return [*memory_data.values()]

    class Config:

        def __init__(self, thread_path: str):
            self.thread_path = thread_path

        async def fetch(self):
            with open(os.path.join(self.thread_path, ".config.json"), "w") as f:
                return json.load(f)

        async def update(self, config):
            with open(os.path.join(self.thread_path, ".config.json"), "w") as f:
                json.dump(config, f, indent=4)
