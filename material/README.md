# Material (Temple OSINT)

- **Category:** OSINT (image identification)
- **Flag:** `0x1337{camphor_wood}`
- **Files:** [`files/temple.jpg`](files/temple.jpg)

## Challenge

> What exact material is this building made of?
>
> The flag is in the format 0x1337{material_name_in_snake_case}. For example, if the material is "Peanut Butter", the flag will be 0x1337{peanut_butter}.

The image (500×375 JPEG) shows a two-tier Japanese temple hall with red pillars, white walls, arched windows, a stone lantern and a white gravel court.

## Solution

1. **Metadata check.** No EXIF, XMP or comments. `binwalk` finds nothing and there is no data after the JPEG end marker. Nothing hidden; this is pure OSINT.
2. **Identify the building.** It is the **Kannon-dō of Hase-dera, Kamakura** (Kanagawa, Japan). Confirmed by comparing with the Wikimedia Commons photo `Kamakura_Hasedera_Kannondou.jpg`: same red pillars, arched windows under the eaves, white panels and stairs at both ends.
3. **Find the material.** This is the trap:
   - The current hall is **reinforced concrete**, rebuilt in 1985–86 after the 1923 Great Kantō Earthquake (official temple site). Rejected.
   - The 本堂 elsewhere on the grounds is pure Taiwan cypress (Japanese Wikipedia). Rejected, different building.
   - Wood-species guesses for the pre-earthquake hall (hinoki, zelkova, cedar) were all rejected.
   - The accepted answer is **camphor wood**: the material of the 9.18 m Eleven-faced Kannon statue enshrined in the hall, carved from a single camphor tree. The setter's "this building made of" points at what the hall is famous for, not its structure.

Flag: `0x1337{camphor_wood}`

## Rejected attempts

`reinforced_concrete`, `concrete`, `ferroconcrete`, `steel_reinforced_concrete`, `taiwan_cypress`, `taiwanese_cypress`, `hinoki`, `japanese_cypress`, `cypress`, `wood`, plus pre-earthquake wood guesses.

## Lessons

- "Exact material" in OSINT challenges often means a specific, Wikipedia-quotable material, not the structural engineering answer.
- Read the English Wikipedia article for the place and note every material it names. Here the only material it mentions is the statue's camphor wood.
- Confirm the building by comparing with a reference photo before researching details.

## Sources

- [Hase-dera (Kamakura), Wikipedia](https://en.wikipedia.org/wiki/Hase-dera_(Kamakura))
- [Hasedera official, about](https://www.hasedera.jp/en/about/)
- [Kannon-dō on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kamakura_Hasedera_Kannondou.jpg)
