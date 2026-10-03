# Never Forget

- **Category:** OSINT
- **Flag:** `0x1337{apex_ceyane}`
- **Files:** [`files/never-forget.zip`](files/never-forget.zip) (contains `garden.png`)

## Challenge

> Thank god it's demolished! Now we finally have a triangular park as planned from december 2006. Flag format is what used to exist before the garden was made, underscore separated 0x1337{name1_name2}.

`garden.png` is a 1185x708 satellite crop. It shows a triangular plot with a newly laid park (curving paths, two lawns, a small circular feature). High-rise residential towers sit on one side, a wide arterial road on another, and a street with parked cars on the third.

## Solution

1. **Read the clues.** A demolition people were glad about, a park that was "as planned" all along, a plan dated December 2006, and a flag of two names. Together these point to two buildings that were put on land meant to be a garden, then torn down.
2. **Match a real event.** That is the Supertech twin towers, **Apex** and **Ceyane**, in the Emerald Court project in Sector 93A, Noida, India:
   - In the original 2006 building plan, the plot was a green area/garden.
   - Supertech later revised the plans and built two towers (Apex, about 32 floors, and Ceyane, about 29) on that land.
   - Emerald Court residents sued. In 2021 the Supreme Court of India ruled the towers illegal, for breaking the minimum distance between buildings and taking the planned green space, and ordered them demolished.
   - They were brought down by controlled implosion on 28 August 2022, and the plot was turned back into a park.
3. **Check the image.** The satellite view fits the site after demolition: a triangular green plot squeezed between the Emerald Court towers and the Noida–Greater Noida Expressway side road. The title, "never forget", fits one of India's most famous demolitions.
4. **Build the flag.** The two names that "used to exist", underscore separated and lowercase: `0x1337{apex_ceyane}`.

## Lessons

- In OSINT, the wording often carries more than the image. "Demolished", "as planned" and a dated plan identified a famous news story before any geolocation was needed.
- When a flag takes names, try lowercase. `apex_ceyane` was accepted.
