# Azathoth

**Azathoth** is a tool for generating, managing, and applying progressive
upgrades to arbitrary sets of YAMLs. It is primarily designed to operate as a
randomizer and upgrader for game settings YAMLs in a Multiworld Madness
challenge.

[Multiworld Madness](https://www.youtube.com/watch?v=XxV5PO94ra4) is a
gaming challenge created by [iateyourpie](https://twitch.tv/iateyourpie) in
which players attempt to complete a solo multiworld randomizer orchestrated via
[Archipelago](https://archipelago.gg). The games involved are typically played
with certain high difficulty settings and further conditions such as not being
permitted to lose any lives. As a reward for reaching milestones in progress,
players can earn upgrades that soften difficulty settings or improve starting
equipment in their games, in the style of a roguelite.

Azathoth simplifies the process of managing these upgrades by handling upgrade
selection, automated YAML editing, and summarization of the results in a single
centralized tool.

## Usage Guide

When Azathoth starts, you'll see two main buttons: **Load Game YAMLs** and
**Load Upgrade Wheel**.

**Load Game YAMLs** prompts you to select the baseline game YAML settings files
that you'll be applying upgrades to. These baseline YAMLs should reflect how
your challenge would be set up if you had no upgrades whatsoever. You should
include all the game YAMLs that you plan to use in your Multiworld Madness.

**Load Upgrade Wheel** prompts you to select the Azathoth Wheel YAML that
defines your particular challenge's possible upgrades. Your Wheel must follow
the [Wheel Schema](#wheel-schema). Upon successfully loading your Wheel, the
[upgrade selector](#upgrade-selector) interface pane will open.

**Exit** exits the program.

### Upgrade Selector

Once an upgrade Wheel is loaded, the upgrade selector opens. Here, every
upgrade possible to earn on your loaded Wheel is listed, grouped by the game to
which they belong.

Upgrades appear next to counters that describe how many times that upgrade
should be applied. Selected upgrades will additionally display the specific
value that they will write to their given YAML address. Counters are bound by
the limits described by your Wheel file for each upgrade and cannot be applied
more times than allowed.

The **Spin** button will produce the given number of upgrades from your Wheel's
weighted random distribution and update your selections to reflect them. Note
that this will clear any selections already made.

The **Clear** button will erase any selections already made and set all
upgrades to a count of `0`.

The **Save** button will apply all selected upgrades to all uploaded game YAMLs
and write new YAML files reflecting these upgrades to the selected output
folder. It will additionally produce a summary file that succinctly collects
the selected upgrades and their values. **BEWARE**: Files written by this
process will overwrite any files of the same name.

## Wheel Schema

Adding upgrades to YAML files requires communicating what upgrades are possible
to earn, how they are selected, what part of a game YAML the upgrade will
alter, and what values they will be set to. Azathoth takes this information in
the form of a **Wheel** file.

The Wheel file, written in YAML, describes exactly one top-level Wheel that
follows the [Wheel schema](#wheel) and the weighted choices that can be spun on
that Wheel.

Azathoth features validation that does its best to identify any problems that
your Wheel file may have. If your Wheel is not set up correctly, address any
errors and warnings produced by the tool.

A common structure for this file starts with a top-level Wheel that separates
upgrades for each individual game into their own individual Wheels, each of
which lists the upgrades available in that game.

An example wheel file might look like this:

```yaml
name: Example Wheel for Azathoth
wheel:
  - game: My First Game
    wheel:
      # Goes up to 20. First upgrade sets to 3, then +1 thereafter.
      - name: Additional Starting Move
        weight: 20
        upgrade:
          path: starting_move_count
          progression:
            atMost: 20
            values: [3]
            increment: 1
      # Goes up to 5. First upgrade sets to 2, then +1 thereafter.
      - name: Additional Starting Character
        weight: 10
        upgrade:
          path: starting_character_count
          progression:
            atMost: 5
            values: [2]
            increment: 1
      # Indefinite upgrade. Starts at 0, then +1 thereafter.
      - name: Start with +1 Banana
        weight: 5
        upgrade:
          path:
            - start_inventory
            - Banana
          progression: ONE_PER
      # This is something we can only ever have once.
      - name: Start with Double Jump
        weight: 1
        upgrade:
          path:
            - start_inventory
            - Double Jump
          progression: UNIQUE
  - game: My Second Game
    wheel:
      # Lets you die once per upgrade without losing. A self-enforced bonus.
      - name: Additional Life
        weight: 5
        upgrade:
          type: manual
          progression: ONE_PER
      # Lowers the damage multiplier by one setting for each upgrade.
      - name: Decrease Damage Multiplier
        weight: 7
        upgrade:
          path: damage_multiplier
          progression:
            values: [double, normal, half]
```

### Wheel

Every Wheel is written as a dict containing the following keys:

- `name` - The display name for the Wheel.
- `game` - The game that upgrades in this Wheel belong to.
- `weight` - The integer weight assigned to this choice on the Wheel above it.
  (_Default: `1`_)
- `wheel` - The list of choices that this Wheel can spin. All entries here are
either other [Wheels](#wheel) or [upgrades](#upgrade).

All Wheels must provide at least one of `name` or `game`. If providing `game`,
it must exactly match the name used by Archipelago YAMLs identifying the game
in question and describes where all upgrades contained by or under this Wheel
will be applied.

### Upgrade

Every upgrade is written as a dict containing the following keys:

- `name` - The display name for the upgrade.
- `weight` - The integer weight assigned to this choice on the Wheel above it.
  (_Default: `1`_)
- `upgrade` - A dict describing an upgrade that you can spin, with these keys:
  - `path` - A list of the nested YAML entries in which to locate this setting.
    Manual* upgrades should not set a `path`.
  - `type` - Set to `manual` when specifying manual* upgrades, otherwise not
     used.
  - `progression` - Describes the value(s) that will be set when receiving this
    upgrade. See [Progressions](#progressions).

\*"Manual" upgrades are upgrades that do not involve changing an actual game
YAML setting. Examples include giving yourself permission to use an
otherwise-restricted tool or to ignore some number of game losses.

Your upgrade's `path` and `progression` ultimately decide what's actually going
to be written in your upgraded YAMLs. If your upgraded YAML is meant to look
something like:

```yaml
Game Title:
  a:
    b:
      c: d
```

Then your `path` should be `[a, b, c]` and your `progression` should describe
what upgraded values could be produced for `d`. The value of `Game Title` is
derived automatically from the nearest containing Wheel's `game` setting. You
may optionally include `Game Title` in your upgrade's `path`, but this is
discouraged.

Upgrades are additive at intermediate levels and overriding at the final level.
In the above example, the contents of `Game Title`, `a`, and `b` would be
unchanged by this upgrade except to set `c` equal to `d`. If `b` contains other
settings, they will not be changed. If `c` already existed, it will be
overwritten by the upgrade and set directly to `d`.

### Progressions

Progressions describe the value that an upgraded setting will be set to if
selected. This includes what to do if an upgrade is allowed to be selected
multiple times and how many times it may be selected.  

Every `Progression` is given _either_ as a dict containing the following keys
_or_ as a [Macro](#progression-macros) string used for common situations.

- `values` - A progressive list of values the upgraded setting will be set to
  if the upgrade is spun that many times.
- `increment` - If set, allows upgrades beyond those specified by `values`,
  adding `increment` to the last entry in `values` for each successive upgrade.
  If `values` is not given, assumes that this baseline value is `0`.
- `limit` - If set, caps the number of times this upgrade can be spun.
- `atMost` - Alternative option to `limit` specifying the highest final value
  that can be permitted.

Theoretically, every progression can be purely defined with `values` alone, but
the other options allow users to concisely describe indefinite behavior and
intended caps without having to write all of that out.

### Progression Macros

Azathoth features macro support for progressions. Certain common progressions
can be given by a simple name instead of giving the entire basic object. The
common progressions supported in this way are given in the following table.

<table>
<tr>
<td>Macro</td> <td>is equvalent to</td> <td>  is used for </td>
</tr>
<tr>
<td>

```yaml
progression: UNIQUE
```

</td>
<td>

```yaml
progression:
  values: [1]
```

</td>
<td>Items that can be collected exactly once.</td>
</tr>

<tr>
<td>

```yaml
progression: ONE_PER
```

</td>
<td>

```yaml
progression:
  increment: 1
```

</td>
<td>
Items that can be collected indefinitely.
</td>
</tr>
</table>

### Additional Requirements

All upgrades must be located beneath a Wheel that specifies a `game` setting.
These need not be the most recent Wheel.

## Known Issues

- No current support for changing upgrades that use lists. Currently only
  upgrades scalars and dicts.

- No current support for making multiple simultaneous changes to different
  parts of the YAML as part of the same upgrade roll.
  - _e.g._ an upgrade that might be stated as "Instead of starting with 1
  `Item X` and 0 `Item Y`, start the game with 0 `Item X` and 1 `Item Y`"

- No known current support for uploading game YAMLs in a single file. I haven't
  tried it, technically, but I wouldn't expect much.

## Troubleshooting

### My YAML Isn't Working Right

YAML can be a real nightmare. As a language, YAML prioritizes readability over
many other qualities including, frustratingly enough, writeability. Its design
includes several choices that lead to ambiguous parsing, choices that can also
differ widely across versions.

As a consequence, this means you can often write the same information in a YAML
in multiple ways. Further, Archipelago's _interpretation_ of YAMLs adds still
more flexibility. If Archipelago files are your first encounter with YAMLs, the
data format can certainly be confusing. If this isn't your first rodeo, they
can still surprise you.

Whenever you're editing YAML files, please keep in mind that whitespace in YAML
is significant and special characters can cause surprising problems. Strings
that include important characters like `:`, `-`, brackets, or braces can cause
issues unless properly escaped. YAML also """"""helpfully"""""" assigns certain
strings special meaning. This includes values such as `false`, `true`, `no`,
`on`, `y`, `off`, and certain colon-separated numbers.

If a particular upgrade or Wheel isn't processing correctly, here's some things
to check:

- Follow any instructions or warnings that Azathoth reports.
- Check your YAML content in a YAML linter to make sure it is valid YAML (_but
  bear in mind that it may **validly** be doing something other than what you
  intended._)
- Double-check that your spacing is consistent. Whitespace matters in YAML.
- Try wrapping your strings with quotes (`'`) or double-quotes (`"`) so the
  value isn't interpreted as something else.

### Hidden Characters

The YAML-parsing library that Azathoth depends on can be flummoxed by the
presence of hidden characters in your input files. This is actually a safety
measure to ensure that the same parser doesn't scan and interpret malicious
instructions that could potentially be hidden in files, so its presence is a
net good thing that can be slightly annoying in certain, benign circumstances.

While scanning in a YAML to this program, you may see perfectly valid-looking
YAML fail with an error like the following:

```text
yaml.parser.ParserError: expected '<document start>', but found '<block mapping start>'
in "<unicode string>", line 28, column 1:
  name: BlasphemousPlayer
  ^
```

This problem can occur when hidden characters are at the head of your file.
YAML is essentially trying to parse these hidden characters as part of your
game options and failing to understand what kind of data the're meant to
represent. If you do not have leading comments in your YAML, these hidden
characters may instead be quietly packed into the name of your output YAML
files' fields, e.g. changing `name:` to `"\xEF\xBB\xBFname:"`.

If you're running into this issue, it's because Azathoth doesn't know yet to
sanitize those fields out for you. You'll want to remove these characters. How
exactly you can do that depends on your text editor, but regular expressions
are probably your ally here.

If you encounter similar errors with different bad field names, please alert
maintainers so the problem can be addressed for future users.

NOTE: Azathoth specifically sanitizes out the byte sequence `\xEF\xBB\xBF` from
the example above. If you're curious, it's the Byte Order Mark (_BOM_)
indicating that the file has been encoded in UTF-8. Most text files don't
include it because many text editors simply assume that a file without a BOM is
encoded in UTF-8 by default and don't bother to state the obvious. A very
common text editor disagrees with this practice.

## Common Questions

### Do I Need To Edit YAMLs to Use Azathoth?

_Sigh._ For now, if you're making your own Wheel, then yes. Sorry.

YAML has [all kinds of problems](#my-yaml-isnt-working-right) that can make it
not always obvious how to implement a change you want.

I wrote Azathoth to help players avoid all of that. You still need to have real
YAMLs for your game settings and a real YAML that describes your Wheel, _but_
these files are shareable. You can write and share these settings with your
friends if you like. A given challenge only needs to have its corresponding
Wheel written just once ever.

NOTE: I'm planning to add tooling to help you write your own Wheel in the near
future.

### Why Doesn't This Use `meta.yaml`?

`meta.yaml` is an Archipelago-specific yaml file that you can include with your
other game files when generating an Archi. Its contents are localized overrides
that will be applied to all instances of the indicated games in the same
multiworld.

So wouldn't it be simpler to just use this for overrides?

Perhaps. But `meta.yaml` has a number of limitations that I felt were simply
avoidable by performing direct YAML editing. Here are a few:

- `meta.yaml` is not recognized by the Archipelago website. Using it requires
  local generation even if your chosen games don't.

- `meta.yaml` does not allow you to add to an existing setting, only override
  it.  If someone wanted to _always_ include `A Really Big Shield` in their
  `start_inventory`, they could never use other upgrades that influence
  `start_inventory` without obliterating that starting setting. Direct YAML
  editing allows us to make additive updates free of destruction.

## Licenses

Azathoth is released under the MIT License. See the file `LICENSE` for details.
