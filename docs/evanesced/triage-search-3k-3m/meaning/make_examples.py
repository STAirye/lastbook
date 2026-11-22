"""Phase A: the example sentences, written from general knowledge, before any test list was opened.
Writes examples.jsonl: {"text", "label": red|yellow|green, "cat"}.
red    = may be life-threatening now (call for help / act now)
yellow = needs care soon, not immediately life-threatening
green  = look-alike non-emergency (idiom, tech, cooking, sport, game, course question, mild symptom, how-to)
"""
import json
from pathlib import Path

RED = {
 'not_breathing': """my son isnt breathing
he stopped breathing what do i do
she is not breathing and her lips are blue
baby not breathing please help
my husband has no pulse
cant feel a heartbeat on him
hes not breathing properly just gasping
grandma making weird gasping noises and wont wake
he breathes like every 10 seconds and doesnt answer
no breath coming out of him
my friend went limp and isnt breathing
how to do cpr on my dad right now
she stopped breathin
he is breating very slow and blue
my baby turned blue and floppy
kid cant breathe at all
he is purple in the face and not breathing
someone collapsed and has no pulse
her chest isnt moving
im doing chest compressions what next
my wife heart stopped
i think hes dead he isnt breathing
cant breath cant breath help
my throat is closing i cant breathe
asthma attack inhaler not working cant talk
he is wheezing and can only say one word at a time
struggling to breathe lips going grey""",
 'choking': """my baby is choking
he is choking on food and cant talk
choking cant cough
she swallowed a coin and cant breathe
toddler choking on a grape
something stuck in his throat he is turning blue
my dad choked on steak and is grabbing his throat
kid swallowed a marble now gagging and cant breath
choking on a fish bone cant breathe
how to do heimlich on a baby now
chokeing help
he is chocking and going red then blue
food went down wrong way and she cant get air
my 2 year old put a battery in his mouth and swallowed it""",
 'unconscious': """my mom collapsed and wont wake up
he fainted and hasnt come round
found my brother unconscious on the floor
she is unresponsive
dad is on the floor and not answering me
my grandpa wont wake up
he passed out and is snoring strangely
she dropped like a stone in the kitchen
guy on the street out cold not moving
my wife blacked out and hit her head
cant wake him up
he keeled over at the table
she slumped in her chair and wont respond
found him face down in the bath
my roommate is unconscious and wont respond to shaking
he went floppy and his eyes rolled back
she is breathing but wont open her eyes
my friend just collapsed while running
old man fell down in the shop and isnt moving
he is not responding to his name""",
 'seizure': """my son is having a seizure
she is fitting and wont stop
he is shaking all over and foaming at the mouth
seizure lasting more than 5 minutes
baby having a fit with a high fever
my wife is convulsing on the floor
he has had three seizures in a row
she is jerking and her eyes are rolling
first time seizure in my dad what do i do
my daughter is twitching and not responsive
epileptic fit wont stop
he had a siezure and isnt waking up after""",
 'bleeding': """bleeding wont stop
he cut his arm and blood is spurting out
my leg is gushing blood
deep cut on the wrist pouring blood
she is bleeding heavily from the head
stab wound in the stomach
he was shot in the leg
blood soaking through the towel
cut an artery i think blood pumping
chainsaw cut his thigh lots of blood
nosebleed for an hour and wont stop
my finger got cut off
his hand was crushed in the machine and bleeding a lot
she is vomiting blood
coughing up lots of blood
throwing up blood and dizzy
bleeding a lot after giving birth
heavy bleeding while pregnant
how to put a tourniquet on fast
glass went into his neck
my friend got stabbed what do i do
bleeding from the ears after he fell
blood everywhere help
hes loosing alot of blood
bleding wont stop from my leg""",
 'chest_pain': """chest pain spreading to my left arm
crushing pain in my chest and sweating
feels like an elephant sitting on my chest
my dad has chest pain and is pale and sweaty
i think im having a heart attack
tight chest and pain going up to my jaw
sudden chest pain and short of breath
heart attack symptoms what do i do
my heart is racing and i feel like im going to pass out
chest pressure and sick and clammy
my husband grabbed his chest and fell down
heart pounding chest pain cant breathe
pain in my chest like a band squeezing
sharp chest pain and coughing blood
my mum says her heart hurts and she is grey
chest hurting really bad and left arm numb""",
 'stroke': """her face is drooping on one side
he cant lift his right arm and speech is slurred
my dad suddenly cant talk properly
i think my mum is having a stroke
sudden worst headache of my life
face crooked and cant smile properly
my grandma cant move one side of her body
he is talking gibberish all of a sudden
sudden confusion and cant understand words
one side of her face went numb and droopy
lost vision in one eye suddenly and arm weak
his words are coming out wrong and his arm is heavy
stroke symptoms right now
thunderclap headache then vomiting
she is dribbling from the side of her mouth and confused""",
 'anaphylaxis': """my throat is swelling after eating peanuts
allergic reaction lips and tongue swelling
stung by a bee and cant breathe
she ate shrimp and her face is swelling up and wheezing
need to use epipen now
hives all over and throat tight
anaphylaxis what do i do
my son is allergic to nuts and just ate one now he is coughing and swelling
swollen tongue cant swallow
after the injection he went red and cant breathe
wasp sting and now dizzy and swelling everywhere
alergic reaction face swelling help""",
 'overdose_poisoning': """he took a whole bottle of pills
my toddler drank bleach
she swallowed a lot of paracetamol
overdose on heroin not breathing
friend took too much and wont wake up
my son ate his grandma's heart pills
baby drank dishwasher liquid
he drank antifreeze
took 30 tylenol an hour ago
she mixed alcohol and sleeping pills and is drowsy
my kid ate some of my medicine
pinpoint pupils and barely breathing after drugs
he snorted something and is having a seizure
fentanyl overdose what do i do
naloxone how to give overdose now
my dog ate rat poison
child swallowed a button battery
drank weed killer
my friend is really drunk and passed out and cold
he cant stop vomiting after drinking all night and is unresponsive
we all have headaches and feel sick near the heater carbon monoxide
smell gas and everyone is dizzy
she breathed in fumes from mixing cleaning products and is coughing
kid ate mushrooms from the garden and is throwing up
she drank kerosene
he swallowed a pack of my antidepressants
ate the whole packet of iron tablets
my brother injected something and turned blue
taken an overdose""",
 'suicide': """i want to kill myself
i dont want to live anymore
im going to end it tonight
i have the pills ready to take them all
my friend says she is going to kill herself
he is talking about hanging himself
i cut myself deep and cant stop the bleeding
thinking about suicide right now
i just want to die
nobody would miss me i am going to end my life
my son wrote a goodbye note
she is standing on the bridge
i took pills to end it
everyone would be better off without me tonight
i cant go on anymore i have a plan
my dad has a gun and says he will use it on himself
i want to disappear forever
how many pills to die""",
 'drowning': """my son fell in the pool and isnt breathing
pulled a kid out of the water not breathing
someone is drowning in the river
baby was under the bath water
he was underwater for a few minutes
swept away by the current
my friend went under at the lake and hasnt come up
child found floating in the pond
fell through the ice into the lake
car went into the river with people inside""",
 'burns': """my child pulled boiling water onto herself
he is on fire
house fire people trapped inside
burnt his whole arm and its white and leathery
her clothes caught fire
chemical burn in the eye
my face got burned by the explosion
big burn on his chest blistering everywhere
burned in a fire and coughing black stuff
electric shock from a power line he is not moving
he got electrocuted and is unconscious
struck by lightning
grease fire burned her hands and face
my toddler grabbed the iron and the burn is huge
smoke inhalation and hoarse voice""",
 'temperature': """he is freezing and stopped shivering and is confused
hypothermia he is not making sense
found her outside in the snow barely conscious
she is very cold and drowsy and slurring
heatstroke he is hot and confused and stopped sweating
collapsed in the heat and is burning up
my dad was working in the sun now he is confused and very hot
baby left in a hot car
very high fever and stiff neck and rash that doesnt fade
fever of 41 and he is delirious
frostbite toes black and he is confused""",
 'head_spine': """fell off the roof and cant move his legs
he hit his head and is vomiting and confused
car crash she cant feel her legs
head injury and one pupil bigger
fell down the stairs and isnt moving
motorbike accident head bleeding not awake
dove into shallow water and cant move
hit his head and now very sleepy and repeating himself
clear fluid coming from his nose after a head injury
baby fell off the bed and is now floppy and sleepy
neck injury after a fall cant feel arms
skull looks dented after he got hit
he was hit by a car
crushed under a car
trapped under rubble after earthquake
tree fell on him""",
 'childbirth': """my water broke and the baby is coming now
baby is coming out what do i do
the cord is coming out first
she is in labour and bleeding a lot
pregnant and very bad stomach pain and bleeding
baby born and not breathing
delivering a baby at home right now
pregnant woman having a seizure
heavy bleeding after the baby came out
pregnant with severe headache and blurry vision and swelling
the baby is coming feet first
newborn is blue and not crying""",
 'child_baby_elderly': """my baby is very floppy and wont feed
newborn has a fever and is not waking for feeds
baby has a rash that doesnt fade under a glass
my infant is grunting and breathing fast
my child is very sleepy and hard to wake
toddler fell into the pool
my baby has a soft spot bulging and is vomiting
baby is limp and pale
child has a high fever and is having a fit
my grandmother fell and cant get up and is confused
old dad is suddenly very confused and cant stand
my baby stopped breathing for a moment and went blue
baby has not peed all day and is very drowsy
little one swallowed a magnet
my newborn is cold and not moving much""",
 'sepsis': """he has a fever and is shivering and confused and his skin is mottled
infection and now she is very drowsy and breathing fast
think he has sepsis
wound is red and spreading and he is feverish and confused
very unwell high temp and skin cold and blotchy
she has not peed and is confused with fever
red streaks up the arm from a cut and fever and dizzy""",
 'diabetic': """my diabetic husband is shaking and sweaty and confused
low blood sugar he is not making sense
she is diabetic and wont wake up
hypo and cant swallow
blood sugar is really high and he is vomiting and drowsy
diabetic and breath smells fruity and breathing fast
my son with diabetes is acting drunk and pale""",
 'trauma_other': """my friend got bitten by a snake
bitten by a rattlesnake leg swelling fast
he got attacked by a dog and is bleeding badly
someone is breaking into my house
a man with a knife is outside
shooting near us
he fell from a ladder and his leg is bent the wrong way and bleeding
bone sticking out of his leg
explosion and people hurt
gas leak and a smell of gas in the house
stomach pain so bad he cant move and belly is hard
severe belly pain and vomiting green
he got hit in the testicles and is in agony and vomiting
my eye got splashed with acid
sudden severe pain in the back and he is pale and fainting
scorpion sting child sweating and drooling
landslide buried a car
building collapsed people stuck""",
 'non_native_slang': """pls help my bro not breathin
mi madre no respira i mean my mother not breath
she fall and no wake
he is dead? no move no breath
my baby no breath help please
blood not stop come out alot
he fell and he not talk
heart attak i think
wife is collaps
he eat poison what i do
plz my kid swalow pills
yo my dude just dropped and aint waking up
bro hes fitting on the floor
help my granpa is turning blue
emergency someone is hurt bad
ambulance now man is dying""",
}

YELLOW = """i cut my finger and it might need stitches
twisted my ankle and it is swollen
think i broke my wrist
burned my hand on the oven small blister
fever of 39 for two days
my child has a high temperature but is playing
vomiting since last night cant keep water down
ear infection pain
bad sore throat and fever
my toddler bumped his head but is acting normal
dog bite on the hand small puncture
stung by a bee and the arm is swollen
rash on the arm spreading slowly
deep splinter in the foot
nosebleed that stopped
sprained my knee playing football
diarrhea for three days
painful urination and fever
tooth knocked out
cut on the head bleeding a little
my back hurts after lifting
burn from boiling water on my hand size of a coin
broken toe
mild asthma flare up inhaler helps
allergic rash but breathing fine
infected cut red and warm
migraine like usual
dizzy when i stand up
fell off my bike and scraped my knee and elbow
my kid has an earache and fever
pink eye
fish hook stuck in my finger
sunburn with blisters
heat exhaustion feel faint and sweaty after a hike
mild frostbite on fingers
my baby has a cold and stuffy nose
stomach bug in the family
cough for a week
dehydrated after running
low grade fever and body aches
broken arm in a child not bleeding
dislocated finger
something in my eye cant get it out
tick bite how to remove
spider bite a bit red
my leg is swollen and painful after a long flight
painful swollen joint
kidney stone pain
blood in my urine
sprained wrist cant move it much
cut my foot on glass
food poisoning since dinner
i think i have flu
chickenpox in my daughter
bad toothache with swelling
stomach ache and fever on the right side
my child swallowed a small piece of plastic but is fine
cracked rib after a fall
concussion mild headache after a knock
headache and stiff shoulders
wound edges wont close
nail went into my foot
sore and swollen after a jellyfish sting
mild burn from a firework
bruised shin
pulled a muscle
hypothermia mild shivering a lot but talking
my elderly mother has a urine infection
uti symptoms
my baby has diarrhea but is drinking
vomited twice
pain in my ear after swimming
nose might be broken after a punch
cut needs butterfly stitches
rash after new medicine itchy
eye is red and painful
gout flare
shingles
high blood pressure reading but feel fine
my kid fell from a tree and his arm hurts
ankle is blue and swollen
stomach cramps after eating
my foot is numb after sitting
cant sleep for days
anxiety attack my heart races but it passes
panic attack how to calm down
i feel very depressed lately
bitten by a cat and it is swelling
blister on my heel infected
sore neck after a car bump yesterday
child has a fever and a mild rash
baby teething fever
dog bit my kid on the leg a little bleeding
whiplash
broken finger
cut lip after a fall
hit my thumb with a hammer
sprain or fracture how to tell
burn on my arm from a pan
fever and chills
my friend is drunk and sick but talking
mild allergic reaction itchy eyes
swallowed a fish bone it scratches
bad period pain
morning sickness cant keep food down
my wound is oozing pus
bump on the head with a lump
fell on my wrist it is swollen and bruised
hand swollen after a bee sting yesterday
chest cold and cough
asthma a bit wheezy
pain on the side when breathing after a cold
my knee gave way and swelled up
cut my thumb with a knife bleeding stopped with pressure
small burn on toddler finger
shin splints
lower back pain shooting down my leg
toothache
sprained ankle hiking far from the car
blisters on my feet
hit my head on a cupboard and have a headache
coughing up green phlegm
sinus infection
vomiting baby once but feeding
rash after hiking itchy poison ivy
fever for 4 days in my kid
earache in the night
snake bite but it was a harmless snake i think
stomach pain for a day
sore wrist after a fall from a skateboard
burnt tongue on hot tea
eye scratch from a branch
my foot got crushed by a box and is bruised
stitches came open a little
infected toenail
hot swollen leg red patch
dizzy and weak since this morning
nausea and headache
i got stung by a jellyfish
cold sore
mild dehydration in my toddler
painful lump in armpit
bleeding gums
swollen glands""".splitlines()

GREEN = {
 'idiom': """my heart stopped when i saw the bill
i almost died laughing
that joke killed me
this traffic is killing me
im dying to know the ending
she broke my heart
i could murder a pizza
the deadline is choking me
drowning in paperwork this week
my head is exploding with all this homework
feeling blue today
that was a stroke of luck
he has a heart of gold
i nearly had a heart attack when the cat jumped out
my feet are killing me after work
im burnt out at work
she took my breath away
cant breathe from laughing so hard
he choked in the final minutes of the game
the company bled money last year
blood is thicker than water meaning
break a leg tonight
i am frozen stiff waiting for the bus lol
that movie was fire
she is drop dead gorgeous
we were dead tired after the trip
my phone is dead
the battery died
i passed out on the couch after the party lol
the market crashed today""",
 'tech': """my computer keeps crashing
blue screen of death on windows
the server is down
how to kill a process in linux
the app froze and wont respond
my laptop is overheating
fatal error when compiling
python script hangs and wont stop
how to bleed edge print in indesign
my phone wont wake from sleep
heartbeat monitor for kubernetes pods
the database connection is dying
choke point in the network
burn an iso to a usb stick
how to resuscitate an old hard drive
kill switch on my vpn
wifi keeps dropping
my game crashed and wont start
memory leak is killing performance
cpu temperature too hot
the website is unresponsive
how to fix a broken pipe error
virus on my computer
stroke width in svg
reset a frozen iphone""",
 'cooking_home': """how long to boil eggs
my bread didnt rise
burnt the rice how to fix
how to bleed a radiator
blood orange cake recipe
let the wine breathe before serving
how to stop pasta boiling over
cut onions without crying
the smoke alarm keeps beeping when i cook
how to put out a candle safely
how to sharpen a kitchen knife
best way to defrost chicken
can i freeze cooked rice
sourdough starter not breathing bubbles
black pudding recipe
how to clean a cast iron pan
my cake collapsed in the oven
how to tenderise steak
how to light a gas stove
kill weeds in the garden
my plants are dying
how to store potatoes for winter
how to purify water for drinking
how to build a fire for cooking outdoors
how to make bone broth""",
 'sport_game': """how to do the backstroke
best chest workout at the gym
how to improve my breathing when running
lung capacity exercises for swimming
how to hold my breath longer underwater for freediving training
my character died in the game how to respawn
how to revive a teammate in fortnite
heal potion recipe minecraft
headshot tips in call of duty
how to choke someone out in jiu jitsu
first blood in league of legends
how to beat the final boss
knockout in boxing scoring rules
how to fall safely in judo
my bike chain broke
how to fix a flat tyre
best hiking boots for winter
how to tie a climbing knot
two stroke engine oil mix
my team got crushed last night""",
 'course_question': """how do you do cpr in general
what are the steps of cpr for a first aid course
how to do the heimlich manoeuvre for a class
first aid course near me
what is the recovery position
what is the ratio of compressions to breaths in cpr
how to recognise a stroke fast acronym
what are the signs of a heart attack
how to make a first aid kit
what should be in a first aid kit for hiking
how to treat a minor burn
what to do if someone faints in general
how long should a tourniquet stay on in theory
practicing cpr on a dummy
what is anaphylaxis
what causes seizures
how does an epipen work
difference between heat exhaustion and heatstroke
how to prevent drowning in children
how to prepare for an earthquake
how to make an emergency plan for the family
how to store water for emergencies
what is hypothermia
how to treat a snake bite in the wild in theory
what is the treatment for burns
signs of concussion to watch for
how to teach kids to call for help
first aid for a nosebleed
how to splint a broken arm
how to stop bleeding from a small cut""",
 'mild_symptom': """i have a mild headache
my nose is runny
slight cough
i feel a bit tired today
my muscles ache after the gym
a small cut on my finger
paper cut
i bit my tongue
mosquito bite itching
hiccups wont stop
i have a little sunburn
dry skin on my hands
my eyes are tired from the screen
i stubbed my toe
mild sore throat
i feel a bit nauseous after the boat
my ears popped on the plane
a bruise on my arm
sneezing a lot from pollen
i have a pimple
my lips are chapped
indigestion after dinner
small blister from new shoes
my back is a bit stiff
i yawn a lot""",
 'everyday_howto': """how to tie a tie
how to change a tyre
how to grow tomatoes
how to start a car with a dead battery
how to sew a button
how to make soap
how to catch fish
how to build a shelter in the woods
how to find north without a compass
how to read a map
how to fix a leaking tap
how to make candles
how to keep chickens
how to make a water filter
how to cut firewood
how to sharpen an axe
how to knit a scarf
what is the capital of france
how to write a cv
how to learn spanish
how to save money
how to bake bread
how to make jam
how to clean mould from a wall
how to raise rabbits""",
 'lookalike_words': """my car battery is dead
my horse is choking on its feed what causes that
the dog is panting a lot in the heat
how to stroke a cat
my fish is floating upside down
the chicken stopped laying eggs
blood pressure normal range
blood type compatibility chart
how to donate blood
heart rate zones for training
how many calories does running burn
what does a pulse oximeter measure
how to take my own pulse
normal breathing rate for adults
how to stop a dripping tap
pressure cooker safety
how to put out a chimney fire safely in theory
my tomato plants have blight
how to bleed brakes on a bike
the patient in my novel has a seizure how should i write it
history of the black death
who invented cpr
book about drowning victims
song about a heart attack
the poison dart frog facts
how venomous are house spiders
is it safe to eat raw eggs
can dogs eat chocolate
how much paracetamol is safe in a day
can i take ibuprofen with food""",
 'figurative_dark_humour': """i want to kill my brother for eating my snack lol
this exam is going to be the death of me
if i hear that song one more time ill die
my mom will kill me if she sees my grades
im so bored i could die
killing time at the airport
i am so hungry i could die
that workout destroyed me
i got destroyed in the match
we are dead in the water with this project""",
 'nonsense_noise': """ok thanks
hello
asdfgh
who are you
sorry wrong chat
lol
what can you do
good morning
test test
thanks that helped""",
}


def main():
    out = []
    seen = set()
    def add(t, lab, cat):
        t = t.strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append({'text': t, 'label': lab, 'cat': cat})
    for cat, block in RED.items():
        for t in block.splitlines():
            add(t, 'red', cat)
    for t in YELLOW:
        add(t, 'yellow', 'yellow')
    for cat, block in GREEN.items():
        for t in block.splitlines():
            add(t, 'green', cat)
    p = Path(__file__).with_name('examples.jsonl')
    with open(p, 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    from collections import Counter
    print(Counter(r['label'] for r in out))


if __name__ == '__main__':
    main()
