from inspect import cleandoc

def get_help():
    text = """Hi, I'm the CoronaBot. You can ask for current info about the novel coronavirus in your area.

            Just type:
                `<command>, <country>, <days_back>`, in a direct message
                or
                `@coronabot <command>, <country>, <days_back>`, in any channel where the bot is

            Where:
             `<command>` is one of:
                 `total` for total cases over time
                 `new` for new cases over time
                 `deaths` for deaths over time
                 `recovered` for recovered numbers over time

            `<country>` is the name of the country you want to ask for

            `<days_back>` (works with 'total' only) reflects the reality from as many days ago (max. 7) as you specify

            For example:
                `total, Brazil, 3`
                `@coronabot: recovered, japan`

            Safe plotting :wink:"""

    return cleandoc(text)

