# CoDEx-S query examples

Each case is the first official query satisfying its stated condition, preferring a fact absent from earlier examples. Cases illustrate the measured groups. The benchmark top answers below use evaluator filtering. Each displayed witness was recovered from the frozen catalog and checked against the positive training graph and rule bindings.

## ComplEx rescues an AnyBURL misrank

`test:6:tail` · (D. H. Lawrence (Q34970), occupation (P106), ?). AnyBURL train-only leading score 0.538, 2 near leaders, known-entity degree 14.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | playwright (Q214917) | playwright (Q214917) |
| all | actor (Q33999) | actor (Q33999) |
| general | journalist (Q1930187) | journalist (Q1930187) |
| constants | actor (Q33999) | actor (Q33999) |
| constants_general | actor (Q33999) | actor (Q33999) |
| frequency | actor (Q33999) | actor (Q33999) |

Held-out answer is **playwright (Q214917)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **playwright (Q214917)** (complex top, held-out answer). `P106(Q34970,Y) <= P106(Q47243,Y)` has native score 0.417 and training support 5. Training witness (Elfriede Jelinek (Q47243), occupation (P106), playwright (Q214917)).
- **actor (Q33999)** (all top, constants top, constants_general top, frequency top). `P106(X,Q33999) <= P106(X,Q28389)` has native score 0.538 and training support 171. Training witness (D. H. Lawrence (Q34970), occupation (P106), screenwriter (Q28389)).
- **journalist (Q1930187)** (general top). `P106(X,Y) <= P737(A,X), P106(A,Y)` has native score 0.331 and training support 452. Training witness (Charles Bukowski (Q76409), influenced by (P737), D. H. Lawrence (Q34970)) · (Charles Bukowski (Q76409), occupation (P106), journalist (Q1930187)).

## Both miss despite a generated answer

`test:0:head` · (?, country of citizenship (P27), France (Q142)). AnyBURL train-only leading score 0.716, 22 near leaders, known-entity degree 325.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Umberto Eco (Q12807) | Jean-Paul Sartre (Q9364) |
| all | Joseph Fourier (Q8772) | Joseph Fourier (Q8772) |
| general | Deryck Whibley (Q216913) | Deryck Whibley (Q216913) |
| constants | Joseph Fourier (Q8772) | Joseph Fourier (Q8772) |
| constants_general | Joseph Fourier (Q8772) | Joseph Fourier (Q8772) |
| frequency | Sebastian Haffner (Q57535) | Sebastian Haffner (Q57535) |

Held-out answer is **Gaspard Monge (Q206832)**.

Native maxplus comparison against the held-out answer fell in the “later score breaks tie” category.

- **Umberto Eco (Q12807)** (complex top). `P27(X,Q142) <= P108(X,Q202660)` has native score 0.704 and training support 19. Training witness (Umberto Eco (Q12807), employer (P108), Collège de France (Q202660)).
- **Joseph Fourier (Q8772)** (all top, constants top, constants_general top). `P27(X,Q142) <= P20(X,Q90)` has native score 0.716 and training support 53. Training witness (Joseph Fourier (Q8772), place of death (P20), Paris (Q90)).
- **Deryck Whibley (Q216913)** (general top). `P27(X,Y) <= P26(A,X), P27(A,Y)` has native score 0.636 and training support 35. Training witness (Avril Lavigne (Q30449), spouse (P26), Deryck Whibley (Q216913)) · (Avril Lavigne (Q30449), country of citizenship (P27), France (Q142)).
- **Sebastian Haffner (Q57535)** (frequency top). `P27(Q57535,Y) <= P17(Q1055,Y)` has native score 0.417 and training support 5. Training witness (Hamburg (Q1055), country (P17), France (Q142)).
- **Gaspard Monge (Q206832)** (held-out answer). `P27(X,Q142) <= P20(X,Q90)` has native score 0.716 and training support 53. Training witness (Gaspard Monge (Q206832), place of death (P20), Paris (Q90)).

## Adding constants corrects the general prediction

`test:2:tail` · (Mos Def (Q38875), occupation (P106), ?). AnyBURL train-only leading score 0.845, 1 near leaders, known-entity degree 14.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | singer (Q177220) | singer (Q177220) |
| all | singer (Q177220) | singer (Q177220) |
| general | writer (Q36180) | writer (Q36180) |
| constants | singer (Q177220) | singer (Q177220) |
| constants_general | singer (Q177220) | singer (Q177220) |
| frequency | writer (Q36180) | writer (Q36180) |

Held-out answer is **singer (Q177220)**.

- **singer (Q177220)** (complex top, all top, constants top, constants_general top, held-out answer). `P106(X,Q177220) <= P1303(X,Q17172850)` has native score 0.845 and training support 470. Training witness (Mos Def (Q38875), instrument (P1303), voice (Q17172850)).
- **writer (Q36180)** (general top). `P106(X,Y) <= P136(X,A), P136(B,A), P106(B,Y)` has native score 0.301 and training support 604. Training witness (Mos Def (Q38875), genre (P136), hip hop music (Q11401)) · (Celeste Buckingham (Q1093318), genre (P136), hip hop music (Q11401)) · (Celeste Buckingham (Q1093318), occupation (P106), writer (Q36180)).
- **writer (Q36180)** (frequency top). `P106(X,Q36180) <= P106(X,Q3282637)` has native score 0.363 and training support 77. Training witness (Mos Def (Q38875), occupation (P106), film producer (Q3282637)).

## Adding constants overrides a correct general prediction

`test:3:tail` · (Max Frisch (Q115483), genre (P136), ?). AnyBURL train-only leading score 0.400, 1 near leaders, known-entity degree 20.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | novel (Q8261) | novel (Q8261) |
| all | powest (Q12799318) | powest (Q12799318) |
| general | prose (Q676) | prose (Q676) |
| constants | powest (Q12799318) | powest (Q12799318) |
| constants_general | powest (Q12799318) | powest (Q12799318) |
| frequency | pop music (Q37073) | pop music (Q37073) |

Held-out answer is **prose (Q676)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **novel (Q8261)** (complex top). `P136(X,Q8261) <= P136(X,Q25379)` has native score 0.300 and training support 6. Training witness (Max Frisch (Q115483), genre (P136), play (Q25379)).
- **powest (Q12799318)** (all top, constants top, constants_general top). `P136(X,Q12799318) <= P136(X,Q25379)` has native score 0.400 and training support 8. Training witness (Max Frisch (Q115483), genre (P136), play (Q25379)).
- **prose (Q676)** (general top, held-out answer). `P136(X,Y) <= P136(X,A), P136(B,A), P136(B,Y)` has native score 0.155 and training support 310. Training witness (Max Frisch (Q115483), genre (P136), play (Q25379)) · (Ivan Andreyevich Krylov (Q191480), genre (P136), play (Q25379)) · (Ivan Andreyevich Krylov (Q191480), genre (P136), prose (Q676)).
- **pop music (Q37073)** (frequency top). `P136(X,Q37073) <= P1412(X,Q652)` has native score 0.120 and training support 9. Training witness (Max Frisch (Q115483), languages spoken, written, or signed (P1412), Italian (Q652)).

## Constants beat the marginal frequency prediction

`test:7:head` · (?, genre (P136), hard rock (Q83270)). AnyBURL train-only leading score 0.500, 7 near leaders, known-entity degree 34.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Myles Kennedy (Q289003) | Myles Kennedy (Q289003) |
| all | Myles Kennedy (Q289003) | Myles Kennedy (Q289003) |
| general | Paula Abdul (Q185465) | Paula Abdul (Q185465) |
| constants | Myles Kennedy (Q289003) | Myles Kennedy (Q289003) |
| constants_general | Myles Kennedy (Q289003) | Myles Kennedy (Q289003) |
| frequency | Daniel Lanois (Q935369) | Daniel Lanois (Q935369) |

Held-out answer is **Myles Kennedy (Q289003)**.

- **Myles Kennedy (Q289003)** (complex top, all top, constants top, constants_general top, held-out answer). `P136(X,Q83270) <= P136(X,Q1133657)` has native score 0.500 and training support 10. Training witness (Myles Kennedy (Q289003), genre (P136), traditional heavy metal (Q1133657)).
- **Paula Abdul (Q185465)** (general top). `P136(X,Y) <= P451(A,X), P3373(A,B), P136(B,Y)` has native score 0.483 and training support 14. Training witness (Jackie Jackson (Q44855), unmarried partner (P451), Paula Abdul (Q185465)) · (Jackie Jackson (Q44855), sibling (P3373), Michael Jackson (Q2831)) · (Michael Jackson (Q2831), genre (P136), hard rock (Q83270)).
- **Daniel Lanois (Q935369)** (frequency top). `P136(Q935369,Y) <= P136(Q1203,Y)` has native score 0.385 and training support 5. Training witness (John Lennon (Q1203), genre (P136), hard rock (Q83270)).

## Frequency wins where constants miss

`test:19:head` · (?, member of (P463), Universal Postal Union (Q17495)). AnyBURL train-only leading score 0.846, 42 near leaders, known-entity degree 160.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Luxembourg (Q32) | Kenya (Q114) |
| all | Taiwan (Q865) | Taiwan (Q865) |
| general | State of Palestine (Q219060) | Ghana (Q117) |
| constants | Taiwan (Q865) | Taiwan (Q865) |
| constants_general | Taiwan (Q865) | Taiwan (Q865) |
| frequency | Luxembourg (Q32) | Luxembourg (Q32) |

Held-out answer is **Luxembourg (Q32)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **Luxembourg (Q32)** (complex top, frequency top, held-out answer). `P463(X,Q17495) <= P530(X,Q38)` has native score 0.831 and training support 64. Training witness (Luxembourg (Q32), diplomatic relation (P530), Italy (Q38)).
- **Taiwan (Q865)** (all top, constants top, constants_general top). `P463(X,Q17495) <= P530(X,Q41)` has native score 0.846 and training support 66. Training witness (Taiwan (Q865), diplomatic relation (P530), Greece (Q41)).
- **State of Palestine (Q219060)** (general top). `P463(X,Y) <= P361(X,A), P361(B,A), P463(B,Y)` has native score 0.684 and training support 540. Training witness (State of Palestine (Q219060), part of (P361), Middle East (Q7204)) · (Bahrain (Q398), part of (P361), Middle East (Q7204)) · (Bahrain (Q398), member of (P463), Universal Postal Union (Q17495)).

## Strong and decisive all-rule evidence

`test:5:tail` · (Julio Iglesias (Q122003), instrument (P1303), ?). AnyBURL train-only leading score 0.667, 1 near leaders, known-entity degree 21.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | guitar (Q6607) | guitar (Q6607) |
| all | guitar (Q6607) | guitar (Q6607) |
| general | guitar (Q6607) | guitar (Q6607) |
| constants | guitar (Q6607) | guitar (Q6607) |
| constants_general | guitar (Q6607) | guitar (Q6607) |
| frequency | guitar (Q6607) | guitar (Q6607) |

Held-out answer is **guitar (Q6607)**.

- **guitar (Q6607)** (complex top, all top, constants top, constants_general top, frequency top, held-out answer). `P1303(X,Q6607) <= P136(X,Q217191)` has native score 0.667 and training support 20. Training witness (Julio Iglesias (Q122003), genre (P136), soft rock (Q217191)).
- **guitar (Q6607)** (general top). `P1303(X,Y) <= P40(X,A), P1303(A,Y)` has native score 0.395 and training support 15. Training witness (Julio Iglesias (Q122003), child (P40), Enrique Iglesias (Q47122)) · (Enrique Iglesias (Q47122), instrument (P1303), guitar (Q6607)).

## Strong but crowded all-rule evidence

`test:1:head` · (?, occupation (P106), mandolinist (Q19723482)). AnyBURL train-only leading score 0.571, 8 near leaders, known-entity degree 16.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Doc Watson (Q465636) | Doc Watson (Q465636) |
| all | Adam Levine (Q219631) | Adam Levine (Q219631) |
| general | Selena Gomez (Q83287) | Selena Gomez (Q83287) |
| constants | Adam Levine (Q219631) | Adam Levine (Q219631) |
| constants_general | Adam Levine (Q219631) | Adam Levine (Q219631) |
| frequency | Johann Wolfgang von Goethe (Q5879) | Johann Wolfgang von Goethe (Q5879) |

Held-out answer is **Leon Russell (Q319374)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **Doc Watson (Q465636)** (complex top). `P106(Q465636,Y) <= P106(Q1373347,Y)` has native score 0.333 and training support 4. Training witness (Martie Maguire (Q1373347), occupation (P106), mandolinist (Q19723482)).
- **Adam Levine (Q219631)** (all top, constants top, constants_general top). `P106(Q219631,Y) <= P106(Q233946,Y)` has native score 0.571 and training support 8. Training witness (Kate Voegele (Q233946), occupation (P106), mandolinist (Q19723482)).
- **Selena Gomez (Q83287)** (general top). `P106(X,Y) <= P451(A,X), P3373(B,A), P106(B,Y)` has native score 0.447 and training support 34. Training witness (Nick Jonas (Q201656), unmarried partner (P451), Selena Gomez (Q83287)) · (Kevin Jonas (Q210172), sibling (P3373), Nick Jonas (Q201656)) · (Kevin Jonas (Q210172), occupation (P106), mandolinist (Q19723482)).
- **Johann Wolfgang von Goethe (Q5879)** (frequency top). `P106(X,Y) <= P106(X,A), P106(B,A), P106(B,Y)` has native score 0.201 and training support 403. Training witness (Johann Wolfgang von Goethe (Q5879), occupation (P106), writer (Q36180)) · (Johnny Cash (Q42775), occupation (P106), writer (Q36180)) · (Johnny Cash (Q42775), occupation (P106), mandolinist (Q19723482)).
- **Leon Russell (Q319374)** (held-out answer). `P106(Q319374,Y) <= P106(Q272031,Y)` has native score 0.385 and training support 5. Training witness (Jack White (Q272031), occupation (P106), mandolinist (Q19723482)).

## High confidence backed by at most ten training facts

`test:8:head` · (?, occupation (P106), producer (Q13235160)). AnyBURL train-only leading score 0.571, 22 near leaders, known-entity degree 60.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Jeff Bridges (Q174843) | Jared Leto (Q484523) |
| all | Dianna Agron (Q228792) | Dianna Agron (Q228792) |
| general | Jada Pinkett Smith (Q228787) | Jada Pinkett Smith (Q228787) |
| constants | Dianna Agron (Q228792) | Dianna Agron (Q228792) |
| constants_general | Dianna Agron (Q228792) | Dianna Agron (Q228792) |
| frequency | Johann Wolfgang von Goethe (Q5879) | Johann Wolfgang von Goethe (Q5879) |

Held-out answer is **J. J. Abrams (Q188137)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **Jeff Bridges (Q174843)** (complex top). `P106(Q174843,Y) <= P106(Q171363,Y)` has native score 0.471 and training support 8. Training witness (Viggo Mortensen (Q171363), occupation (P106), producer (Q13235160)).
- **Dianna Agron (Q228792)** (all top, constants top, constants_general top). `P106(Q228792,Y) <= P106(Q37876,Y)` has native score 0.571 and training support 8. Training witness (Natalie Portman (Q37876), occupation (P106), producer (Q13235160)).
- **Jada Pinkett Smith (Q228787)** (general top). `P106(X,Y) <= P40(X,A), P40(B,A), P106(B,Y)` has native score 0.535 and training support 38. Training witness (Jada Pinkett Smith (Q228787), child (P40), Jaden Smith (Q221364)) · (Will Smith (Q40096), child (P40), Jaden Smith (Q221364)) · (Will Smith (Q40096), occupation (P106), producer (Q13235160)).
- **Johann Wolfgang von Goethe (Q5879)** (frequency top). `P106(Q5879,Y) <= P106(Q51094,Y)` has native score 0.214 and training support 3. Training witness (Yuri Shevchuk (Q51094), occupation (P106), producer (Q13235160)).
- **J. J. Abrams (Q188137)** (held-out answer). `P106(Q188137,Y) <= P106(Q36949,Y)` has native score 0.400 and training support 6. Training witness (Robert De Niro (Q36949), occupation (P106), producer (Q13235160)).

## Selector improves the train-only prediction

`test:12:head` · (?, record label (P264), Hollywood Records (Q387539)). AnyBURL train-only leading score 0.379, 2 near leaders, known-entity degree 15.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Laura Marano (Q242792) | Miley Cyrus (Q4235) |
| all | Kevin Jonas (Q210172) | Kevin Jonas (Q210172) |
| general | Kevin Jonas (Q210172) | Kevin Jonas (Q210172) |
| constants | Lea Salonga (Q294144) | Miley Cyrus (Q4235) |
| constants_general | Kevin Jonas (Q210172) | Kevin Jonas (Q210172) |
| frequency | Cher (Q12003) | Cher (Q12003) |

Held-out answer is **Kevin Jonas (Q210172)**.

- **Laura Marano (Q242792)** (complex top). `P264(X,Q387539) <= P264(X,Q54860)` has native score 0.263 and training support 5. Training witness (Laura Marano (Q242792), record label (P264), Walt Disney Records (Q54860)).
- **Kevin Jonas (Q210172)** (all top, general top, constants_general top, held-out answer). `P264(X,Y) <= P3373(A,X), P451(A,B), P264(B,Y)` has native score 0.379 and training support 11. Training witness (Nick Jonas (Q201656), sibling (P3373), Kevin Jonas (Q210172)) · (Nick Jonas (Q201656), unmarried partner (P451), Selena Gomez (Q83287)) · (Selena Gomez (Q83287), record label (P264), Hollywood Records (Q387539)).
- **Lea Salonga (Q294144)** (constants top). `P264(X,Q387539) <= P264(X,Q54860)` has native score 0.263 and training support 5. Training witness (Lea Salonga (Q294144), record label (P264), Walt Disney Records (Q54860)).
- **Cher (Q12003)** (frequency top). `P264(Q12003,Y) <= P17(Y,Q30)` has native score 0.125 and training support 5. Training witness (Hollywood Records (Q387539), country (P17), United States of America (Q30)).

## Selector harms the train-only prediction

`test:31:head` · (?, diplomatic relation (P530), Germany (Q183)). AnyBURL train-only leading score 0.876, 33 near leaders, known-entity degree 480.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Japan (Q17) | Japan (Q17) |
| all | Japan (Q17) | Spain (Q29) |
| general | Japan (Q17) | Japan (Q17) |
| constants | Japan (Q17) | Spain (Q29) |
| constants_general | Japan (Q17) | Spain (Q29) |
| frequency | Germany (Q183) | Germany (Q183) |

Held-out answer is **Japan (Q17)**.

- **Japan (Q17)** (complex top, all top, constants top, constants_general top, held-out answer). `P530(X,Q183) <= P530(Q183,X)` has native score 0.876 and training support 148. Training witness (Germany (Q183), diplomatic relation (P530), Japan (Q17)).
- **Japan (Q17)** (general top). `P530(X,Y) <= P530(Y,X)` has native score 0.867 and training support 1532. Training witness (Germany (Q183), diplomatic relation (P530), Japan (Q17)).

## Applicable symmetry rule

`test:9:head` · (?, diplomatic relation (P530), Thailand (Q869)). AnyBURL train-only leading score 0.867, 4 near leaders, known-entity degree 60.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Malaysia (Q833) | Russia (Q159) |
| all | Malaysia (Q833) | Russia (Q159) |
| general | Malaysia (Q833) | Germany (Q183) |
| constants | Malaysia (Q833) | Russia (Q159) |
| constants_general | Malaysia (Q833) | Russia (Q159) |
| frequency | United States of America (Q30) | Germany (Q183) |

Held-out answer is **Malaysia (Q833)**.

- **Malaysia (Q833)** (complex top, all top, general top, constants_general top, held-out answer). `P530(X,Y) <= P530(Y,X)` has native score 0.867 and training support 1532. Training witness (Thailand (Q869), diplomatic relation (P530), Malaysia (Q833)).
- **Malaysia (Q833)** (constants top). `P530(Q833,Y) <= P530(Y,Q833)` has native score 0.817 and training support 67. Training witness (Thailand (Q869), diplomatic relation (P530), Malaysia (Q833)).
- **United States of America (Q30)** (frequency top). `P530(Q30,Y) <= P530(Q148,Y)` has native score 0.796 and training support 109. Training witness (People's Republic of China (Q148), diplomatic relation (P530), Thailand (Q869)).
- **Russia (Q159)** (symmetry). `P530(X,Y) <= P530(Y,X)` has native score 0.867 and training support 1532. Training witness (Thailand (Q869), diplomatic relation (P530), Russia (Q159)).

## Applicable inversion rule

`test:13:head` · (?, record label (P264), Warner Music Group (Q21077)). AnyBURL train-only leading score 0.333, 5 near leaders, known-entity degree 32.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Alanis Morissette (Q130742) | Cher (Q12003) |
| all | Frank Sinatra (Q40912) | Cher (Q12003) |
| general | Warner Bros. (Q126399) | Warner Bros. (Q126399) |
| constants | Frank Sinatra (Q40912) | Cher (Q12003) |
| constants_general | Frank Sinatra (Q40912) | Cher (Q12003) |
| frequency | John Lennon (Q1203) | Cher (Q12003) |

Held-out answer is **Kenny Rogers (Q217160)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **Alanis Morissette (Q130742)** (complex top). `P264(Q130742,Y) <= P264(Q286022,Y)` has native score 0.200 and training support 2. Training witness (Common (Q286022), record label (P264), Warner Music Group (Q21077)).
- **Frank Sinatra (Q40912)** (all top, constants top, constants_general top). `P264(Q40912,Y) <= P264(Q310300,Y)` has native score 0.333 and training support 3. Training witness (James Taylor (Q310300), record label (P264), Warner Music Group (Q21077)).
- **Warner Bros. (Q126399)** (general top, inversion). `P264(X,Y) <= P112(Y,X)` has native score 0.250 and training support 3. Training witness (Warner Music Group (Q21077), founded by (P112), Warner Bros. (Q126399)).
- **John Lennon (Q1203)** (frequency top). `P264(Q1203,Y) <= P264(Q11998,Y)` has native score 0.300 and training support 3. Training witness (Kylie Minogue (Q11998), record label (P264), Warner Music Group (Q21077)).
- **Kenny Rogers (Q217160)** (held-out answer). `P264(Q217160,Y) <= P264(Q310300,Y)` has native score 0.222 and training support 2. Training witness (James Taylor (Q310300), record label (P264), Warner Music Group (Q21077)).

## Applicable subsumption rule

`test:4:head` · (?, location of formation (P740), Soviet Union (Q15180)). AnyBURL train-only leading score 0.015, 3 near leaders, known-entity degree 140.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Reprise Records (Q645889) | Reprise Records (Q645889) |
| all | Moscow (Q649) | Moscow (Q649) |
| general | Moscow (Q649) | Moscow (Q649) |
| constants | abstained | abstained |
| constants_general | Moscow (Q649) | Moscow (Q649) |
| frequency | Aaliyah (Q11617) | Aaliyah (Q11617) |

Held-out answer is **Bulat Okudzhava (Q239652)**.

- **Moscow (Q649)** (all top, general top, constants_general top, subsumption). `P740(X,Y) <= P17(X,Y)` has native score 0.015 and training support 2. Training witness (Moscow (Q649), country (P17), Soviet Union (Q15180)).

## Applicable two-hop composition rule

`test:18:head` · (?, ethnic group (P172), African Americans (Q49085)). AnyBURL train-only leading score 0.667, 23 near leaders, known-entity degree 144.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Jason Derulo (Q243639) | Jason Derulo (Q243639) |
| all | Randy Jackson (Q349461) | Jackie Jackson (Q44855) |
| general | Randy Jackson (Q349461) | Jackie Jackson (Q44855) |
| constants | Jason Derulo (Q243639) | Jason Derulo (Q243639) |
| constants_general | Randy Jackson (Q349461) | Jackie Jackson (Q44855) |
| frequency | Lauren Bacall (Q104000) | Lauren Bacall (Q104000) |

Held-out answer is **Charlie Wilson (Q1067043)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **Jason Derulo (Q243639)** (complex top, constants top). `P172(X,Q49085) <= P106(X,Q2252262)` has native score 0.618 and training support 42. Training witness (Jason Derulo (Q243639), occupation (P106), rapper (Q2252262)).
- **Randy Jackson (Q349461)** (all top, general top, constants_general top). `P172(X,Y) <= P3373(A,X), P40(B,A), P172(B,Y)` has native score 0.667 and training support 14. Training witness (Jackie Jackson (Q44855), sibling (P3373), Randy Jackson (Q349461)) · (Joe Jackson (Q361297), child (P40), Jackie Jackson (Q44855)) · (Joe Jackson (Q361297), ethnic group (P172), African Americans (Q49085)).
- **Lauren Bacall (Q104000)** (frequency top). `P172(X,Q49085) <= P106(X,Q4610556)` has native score 0.240 and training support 23. Training witness (Lauren Bacall (Q104000), occupation (P106), model (Q4610556)).
- **Charlie Wilson (Q1067043)** (held-out answer). `P172(X,Q49085) <= P136(X,Q131272)` has native score 0.532 and training support 42. Training witness (Charlie Wilson (Q1067043), genre (P136), soul music (Q131272)).
- **Jackie Jackson (Q44855)** (two-hop composition). `P172(X,Y) <= P40(A,X), P172(A,Y)` has native score 0.591 and training support 13. Training witness (Joe Jackson (Q361297), child (P40), Jackie Jackson (Q44855)) · (Joe Jackson (Q361297), ethnic group (P172), African Americans (Q49085)).

## Applicable three-hop composition rule

`test:10:head` · (?, member of (P463), International Finance Corporation (Q656801)). AnyBURL train-only leading score 0.875, 35 near leaders, known-entity degree 165.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Madagascar (Q1019) | Barbados (Q244) |
| all | Madagascar (Q1019) | Kenya (Q114) |
| general | Madagascar (Q1019) | Tanzania (Q924) |
| constants | Madagascar (Q1019) | Kenya (Q114) |
| constants_general | Madagascar (Q1019) | Kenya (Q114) |
| frequency | Netherlands (Q55) | Italy (Q38) |

Held-out answer is **Madagascar (Q1019)**.

- **Madagascar (Q1019)** (complex top, all top, constants top, constants_general top, held-out answer). `P463(X,Q656801) <= P463(X,Q340195)` has native score 0.875 and training support 70. Training witness (Madagascar (Q1019), member of (P463), African Development Bank (Q340195)).
- **Madagascar (Q1019)** (general top, three-hop composition). `P463(X,Y) <= P361(X,A), P361(B,A), P463(B,Y)` has native score 0.684 and training support 540. Training witness (Madagascar (Q1019), part of (P361), East Africa (Q27407)) · (Malawi (Q1020), part of (P361), East Africa (Q27407)) · (Malawi (Q1020), member of (P463), International Finance Corporation (Q656801)).
- **Netherlands (Q55)** (frequency top). `P463(X,Q656801) <= P463(X,Q340195)` has native score 0.875 and training support 70. Training witness (Netherlands (Q55), member of (P463), African Development Bank (Q340195)).

## Exclusive success on languages spoken, written, or signed (P1412)

`test:30:head` · (?, languages spoken, written, or signed (P1412), German (Q188)). AnyBURL train-only leading score 0.756, 21 near leaders, known-entity degree 210.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Franz Miklosich (Q93401) | Heinrich Brunner (Q94701) |
| all | Christa Wolf (Q57382) | Christa Wolf (Q57382) |
| general | Christa Wolf (Q57382) | Christa Wolf (Q57382) |
| constants | Christa Wolf (Q57382) | Christa Wolf (Q57382) |
| constants_general | Christa Wolf (Q57382) | Christa Wolf (Q57382) |
| frequency | Omar Sharif (Q170515) | Heinrich Schliemann (Q57106) |

Held-out answer is **Christa Wolf (Q57382)**.

- **Franz Miklosich (Q93401)** (complex top). `P1412(X,Q188) <= P27(X,Q40)` has native score 0.630 and training support 17. Training witness (Franz Miklosich (Q93401), country of citizenship (P27), Austria (Q40)).
- **Christa Wolf (Q57382)** (all top, constants top, constants_general top, held-out answer). `P1412(X,Q188) <= P27(X,Q183)` has native score 0.756 and training support 68. Training witness (Christa Wolf (Q57382), country of citizenship (P27), Germany (Q183)).
- **Christa Wolf (Q57382)** (general top). `P1412(X,Y) <= P27(X,A), P17(B,A), P37(B,Y)` has native score 0.703 and training support 239. Training witness (Christa Wolf (Q57382), country of citizenship (P27), Germany (Q183)) · (Berlin (Q64), country (P17), Germany (Q183)) · (Berlin (Q64), official language (P37), German (Q188)).
- **Omar Sharif (Q170515)** (frequency top). `P1412(Q170515,Y) <= P1412(Q156774,Y)` has native score 0.417 and training support 5. Training witness (Pedro II of Brazil (Q156774), languages spoken, written, or signed (P1412), German (Q188)).

## Exclusive success on diplomatic relation (P530)

`test:17:tail` · (Bosnia and Herzegovina (Q225), diplomatic relation (P530), ?). AnyBURL train-only leading score 0.867, 3 near leaders, known-entity degree 50.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Georgia (Q230) | Georgia (Q230) |
| all | Indonesia (Q252) | Indonesia (Q252) |
| general | Georgia (Q230) | Georgia (Q230) |
| constants | Indonesia (Q252) | Indonesia (Q252) |
| constants_general | Indonesia (Q252) | Indonesia (Q252) |
| frequency | People's Republic of China (Q148) | People's Republic of China (Q148) |

Held-out answer is **Indonesia (Q252)**.

- **Georgia (Q230)** (complex top, general top). `P530(X,Y) <= P530(Y,X)` has native score 0.867 and training support 1532. Training witness (Georgia (Q230), diplomatic relation (P530), Bosnia and Herzegovina (Q225)).
- **Indonesia (Q252)** (all top, constants_general top, held-out answer). `P530(X,Y) <= P530(Y,X)` has native score 0.867 and training support 1532. Training witness (Indonesia (Q252), diplomatic relation (P530), Bosnia and Herzegovina (Q225)).
- **Indonesia (Q252)** (constants top). `P530(X,Q252) <= P530(Q252,X)` has native score 0.833 and training support 60. Training witness (Indonesia (Q252), diplomatic relation (P530), Bosnia and Herzegovina (Q225)).
- **People's Republic of China (Q148)** (frequency top). `P530(X,Q148) <= P530(Q35,X)` has native score 0.761 and training support 70. Training witness (Denmark (Q35), diplomatic relation (P530), Bosnia and Herzegovina (Q225)).

## Exclusive success on country of citizenship (P27)

`test:37:head` · (?, country of citizenship (P27), German Empire (Q43287)). AnyBURL train-only leading score 0.533, 4 near leaders, known-entity degree 27.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | Carl Orff (Q44086) | Carl Orff (Q44086) |
| all | Erika Mann (Q61597) | Erika Mann (Q61597) |
| general | Erika Mann (Q61597) | Erika Mann (Q61597) |
| constants | Carl Orff (Q44086) | Carl Orff (Q44086) |
| constants_general | Erika Mann (Q61597) | Erika Mann (Q61597) |
| frequency | Elie Wiesel (Q18391) | Elie Wiesel (Q18391) |

Held-out answer is **Carl Orff (Q44086)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **Carl Orff (Q44086)** (complex top, constants top, held-out answer). `P27(X,Q43287) <= P27(X,Q7318)` has native score 0.467 and training support 7. Training witness (Carl Orff (Q44086), country of citizenship (P27), Nazi Germany (Q7318)).
- **Erika Mann (Q61597)** (all top, general top, constants_general top). `P27(X,Y) <= P40(A,X), P27(A,Y)` has native score 0.533 and training support 16. Training witness (Thomas Mann (Q37030), child (P40), Erika Mann (Q61597)) · (Thomas Mann (Q37030), country of citizenship (P27), German Empire (Q43287)).
- **Elie Wiesel (Q18391)** (frequency top). `P27(X,Y) <= P1412(X,A), P1412(B,A), P27(B,Y)` has native score 0.176 and training support 353. Training witness (Elie Wiesel (Q18391), languages spoken, written, or signed (P1412), English (Q1860)) · (Marlene Dietrich (Q4612), languages spoken, written, or signed (P1412), English (Q1860)) · (Marlene Dietrich (Q4612), country of citizenship (P27), German Empire (Q43287)).

## Exclusive success on member of (P463)

`test:14:tail` · (Victor Ambartsumian (Q164396), member of (P463), ?). AnyBURL train-only leading score 0.709, 1 near leaders, known-entity degree 15.

| Model | Benchmark top | Train-only top |
| --- | --- | --- |
| complex | German Academy of Sciences Leopoldina (Q543804) | German Academy of Sciences Leopoldina (Q543804) |
| all | Royal Prussian Academy of Sciences (Q329464) | American Academy of Arts and Sciences (Q463303) |
| general | USSR Union of Writers (Q1425328) | USSR Union of Writers (Q1425328) |
| constants | Royal Prussian Academy of Sciences (Q329464) | American Academy of Arts and Sciences (Q463303) |
| constants_general | Royal Prussian Academy of Sciences (Q329464) | American Academy of Arts and Sciences (Q463303) |
| frequency | United Nations (Q1065) | American Academy of Arts and Sciences (Q463303) |

Held-out answer is **German Academy of Sciences Leopoldina (Q543804)**.

Native maxplus comparison against the held-out answer fell in the “higher leading score” category.

- **German Academy of Sciences Leopoldina (Q543804)** (complex top, held-out answer). `P463(Q164396,Y) <= P463(Q48990,Y)` has native score 0.455 and training support 5. Training witness (Nikolay Semyonov (Q48990), member of (P463), German Academy of Sciences Leopoldina (Q543804)).
- **Royal Prussian Academy of Sciences (Q329464)** (all top, constants top, constants_general top). `P463(X,Q329464) <= P463(X,Q188771)` has native score 0.557 and training support 34. Training witness (Victor Ambartsumian (Q164396), member of (P463), French Academy of Sciences (Q188771)).
- **USSR Union of Writers (Q1425328)** (general top). `P463(X,Y) <= P463(X,A), P463(B,A), P463(B,Y)` has native score 0.375 and training support 751. Training witness (Victor Ambartsumian (Q164396), member of (P463), Russian Academy of Sciences (Q83172)) · (Michail Sholokhov (Q42398), member of (P463), Russian Academy of Sciences (Q83172)) · (Michail Sholokhov (Q42398), member of (P463), USSR Union of Writers (Q1425328)).
- **United Nations (Q1065)** (frequency top). `P463(X,Q1065) <= P463(X,A)` has native score 0.028 and training support 179. Training witness (Victor Ambartsumian (Q164396), member of (P463), German Academy of Sciences at Berlin (Q49738)).

