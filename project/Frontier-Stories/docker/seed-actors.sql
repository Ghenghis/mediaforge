-- Sample Actors Seeding Script for Frontier-Stories
-- Run this to populate the database with initial actors

-- Clear existing actors (optional)
-- DELETE FROM public.actors;

-- Insert sample Old West actors
INSERT INTO public.actors (first_name, last_name, role, era, ethnicity, bio) VALUES
('John', 'Marston', 'Cowboy', '1870s', 'Caucasian', 'Former outlaw turned rancher, skilled with revolver and lasso'),
('Mary', 'Sullivan', 'Saloon Owner', '1870s', 'Irish', 'Runs the local saloon, knows everyone''s secrets in town'),
('Thomas', 'Blackwood', 'Sheriff', '1870s', 'Caucasian', 'Former Union soldier, maintains law and order in the frontier town'),
('Sarah', 'Running Deer', 'Native American Guide', '1870s', 'Native American', 'Tribal elder''s daughter, expert tracker and healer'),
('James', 'McLeod', 'Gold Prospector', '1870s', 'Scottish', 'Experienced prospector searching for the mother lode'),
('Elizabeth', 'Hawthorne', 'School Teacher', '1870s', 'Caucasian', 'Educated woman from the East, teaches town''s children'),
('Miguel', 'Rodriguez', 'Cattle Rancher', '1870s', 'Hispanic', 'Owns a large cattle ranch, respected businessman'),
('Wang', 'Chen', 'Railroad Worker', '1870s', 'Chinese', 'Skilled laborer building the transcontinental railroad'),
('Rebecca', 'Thompson', 'Doctor', '1870s', 'Caucasian', 'One of the few female doctors in the territory'),
('Joseph', 'Crow Feather', 'Native American Warrior', '1870s', 'Native American', 'Fierce warrior protecting tribal lands'),
('Samuel', 'Jones', 'Preacher', '1870s', 'African American', 'Traveling minister bringing faith to the frontier'),
('Clara', 'O''Malley', 'Hotel Owner', '1870s', 'Irish', 'Widow who runs the town''s only hotel'),
('Robert', 'Jackson', 'Banker', '1870s', 'Caucasian', 'Controls the town''s money, influential citizen'),
('Nakoma', 'Bright Star', 'Native American Medicine Woman', '1870s', 'Native American', 'Traditional healer with deep knowledge of herbs'),
('William', 'Turner', 'Blacksmith', '1870s', 'Caucasian', 'Essential craftsman, fixes everything from tools to weapons'),
('Maria', 'Gonzalez', 'General Store Owner', '1870s', 'Hispanic', 'Sells supplies to townsfolk and travelers'),
('Henry', 'Morgan', 'Stagecoach Driver', '1870s', 'Caucasian', 'Braves dangerous roads to deliver mail and passengers'),
('Grace', 'Wilson', 'Telegraph Operator', '1870s', 'Caucasian', 'Connects the town to the outside world through Morse code'),
('Daniel', 'Two Bears', 'Native American Hunter', '1870s', 'Native American', 'Provides food for his tribe and trades with settlers'),
('Margaret', ''Brown', 'Homesteader', '1870s', 'Caucasian', 'Tough pioneer woman building a new life on the prairie'),
('Carlos', 'Mendoza', 'Bandit', '1870s', 'Hispanic', 'Notorious outlaw who robs stagecoaches and banks'),
('Emily', 'Parker', 'Journalist', '1870s', 'Caucasian', 'Writes about frontier life for Eastern newspapers'),
('Sam', 'Cole', 'Cattle Rustler', '1870s', 'Caucasian', 'Skilled horseman who steals cattle for a living'),
('Anna', 'Lee', 'Laundress', '1870s', 'Chinese', 'Washes clothes for miners and townsfolk'),
('Benjamin', 'Carter', 'Land Surveyor', '1870s', 'Caucasian', 'Maps the territory for future development'),
('Sofia', 'Martinez', 'Ranch Wife', '1870s', 'Hispanic', 'Manages household and helps with ranch work'),
('Thomas', 'Murphy', 'Miner', '1870s', 'Irish', 'Works the silver mines hoping to strike it rich'),
('Rachel', 'Green', 'Midwife', '1870s', 'Caucasian', 'Delivers babies and provides medical care to women'),
('Jacob', 'Wolf', 'Native American Scout', '1870s', 'Native American', 'Serves as guide for Army expeditions'),
('Louisa', 'Baker', 'Baker', '1870s', 'Caucasian', 'Provides fresh bread and pastries for the town'),
('George', 'Washington', 'Buffalo Soldier', '1870s', 'African American', 'Army sergeant serving on the frontier'),
('Teresa', 'Flores', 'Cantina Owner', '1870s', 'Hispanic', 'Runs a popular eating and drinking establishment'),
('Edward', 'Hawkins', 'Trader', '1870s', 'Caucasian', 'Trades goods between settlers and Native Americans'),
('Winona', 'Spirit Woman', 'Native American Storyteller', '1870s', 'Native American', 'Keeps tribal history alive through oral traditions'),
('Frank', 'Miller', 'Livery Stable Owner', '1870s', 'Caucasian', 'Provides horses and boarding for travelers'),
('Isabella', 'Romano', 'Dance Hall Girl', '1870s', 'Hispanic', 'Entertains miners and cowboys in the dance hall'),
('Samuel', 'Taylor', 'Judge', '1870s', 'Caucasian', 'Brings law and justice to the frontier town'),
('Katherine', 'O''Brien', 'Seamstress', '1870s', 'Irish', 'Makes and mends clothes for the community'),
('James', 'Parker', 'Mountain Man', '1870s', 'Caucasian', 'Lives in the wilderness, traps and trades furs'),
('Maria', 'Santiago', 'Cook', '1870s', 'Hispanic', 'Works at the ranch feeding hungry cowboys'),
('Robert', 'Grant', 'Army Officer', '1870s', 'Caucasian', 'Commands the local Army fort'),
('Dawn', 'Morning Star', 'Native American Weaver', '1870s', 'Native American', 'Creates beautiful blankets and baskets'),
('Charles', 'Cole', 'Ranch Hand', '1870s', 'Caucasian', 'Hardworking cowboy who tends cattle'),
('Elena', 'Vargas', 'Healer', '1870s', 'Hispanic', 'Uses traditional remedies to treat the sick'),
('William', ''Anderson', 'Gunsmith', '1870s', 'Caucasian', 'Crafts and repairs firearms for the town'),
('Patricia', 'Murphy', 'Saloon Girl', '1870s', 'Irish', 'Serves drinks and entertains customers'),
('Samuel', 'Brown', 'Missions Priest', '1870s', 'Caucasian', 'Runs the local mission and converts natives'),
('Tess', 'Red Feather', 'Native American Pottery Maker', '1870s', 'Native American', 'Creates beautiful pottery for trade'),
('Jack', 'Wilson', 'Deputy Sheriff', '1870s', 'Caucasian', 'Assists the sheriff in maintaining order'),
('Rosa', 'Diaz', 'Farm Wife', '1870s', 'Hispanic', 'Works the family farm with her husband'),
('Benjamin', 'Clark', 'Explorer', '1870s', 'Caucasian', 'Maps uncharted territories in the West'),
('Susan', 'White', 'Fort Wife', '1870s', 'Caucasian', 'Wife of Army officer, manages fort life'),
('Thomas', 'Red Cloud', 'Native American Chief', '1870s', 'Native American', 'Leads his tribe through difficult times');

-- Update the sequence for future inserts
SELECT setval('actors_id_seq', (SELECT MAX(id) FROM public.actors));

-- Verify insertion
SELECT COUNT(*) as total_actors_inserted FROM public.actors;
