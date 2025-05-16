My co-workers and I have been working on an AI Programming Assistant called Sketch for the last few months. The thing I've been most surprised by is how shockingly simple the main loop of using an LLM with tool use is:

``` python
def loop(llm):
    msg = user_input()
    while True:
        output, tool_calls = llm(msg)
        print("Agent: ", output)
        if tool_calls:
            msg = [ handle_tool_call(tc) for tc in tool_calls ]
        else:
            msg = user_input()
```
There's some pomp and circumstance to make the above work [here's the full script,](agent_loop.py) but the core idea is the above 9 lines. Here, llm() is a function that sends the system prompt, the conversation so far, and the next message to the LLM API.

Tool use is the fancy term for "the LLM returns some output that corresponds to a schema," and, in the full script, we tell the LLM (in its system prompt and tool description prompts) that it has access to bash.

With just that one very general purpose tool, the current models (we use Claude 3.7 Sonnet extensively) can nail many problems, some of them in "one shot." Whereas I used to look up an esoteric git operation and then cut and paste, now I just ask Sketch to do it. Whereas I used to handle git merges manually, now I let Sketch take a first pass. Whereas I used to change a type and go through the resulting type checker errors one by one (or, let's be real, with perl -pie ridiculousness), I give it a shot with Sketch. If appropriately prompted, the agentic loop can be persistent. If you don't have some tool installed, it'll install it. If your grep has different command line options, it adapts. (It can also be infuriating! "Oh, this test doesn't pass... let's just skip it," it sometimes says, maddeningly.)

For many workflows, agentic tools specialize. Sketch's quiver of tools is not just bash, as we've found that a handful of extra tools improve the quality, speed up iterations, and facilitate better developer workflows. Tools that let the LLM edit text correctly are surprisingly tricky. Seeing the LLM struggle with sed one-liners re-affirms that visual (as opposed to line) editors are a marvel.

I have no doubt that agent loops will get incorporated into more day to day automation tedium that's historically been too specific for general purpose tools and too esoteric and unstable to automate traditionally. I keep thinking of how much time I've spent correlating stack traces with git commits, and how good LLMs are at doing a first pass on it. We'll be seeing more custom, ad hoc, throw-away LLM agent loops in our bin/ directories. Grab your favorite bearer token and give it a shot.