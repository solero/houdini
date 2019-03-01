DROP TABLE IF EXISTS item;
CREATE TABLE item (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30),
  "Type" SMALLINT NOT NULL DEFAULT 1,
  "Cost" SMALLINT NOT NULL DEFAULT 0,
  "Member" BOOLEAN NOT NULL DEFAULT FALSE,
  "Bait" BOOLEAN NOT NULL DEFAULT FALSE,
  "Patched" BOOLEAN NOT NULL DEFAULT FALSE,
  "EPF" BOOLEAN NOT NULL DEFAULT FALSE,
  "Tour" BOOLEAN NOT NULL DEFAULT FALSE,
  "ReleaseDate" DATE NOT NULL,
  PRIMARY KEY ("ID")
);

ALTER TABLE item ALTER COLUMN "ReleaseDate" SET DEFAULT now();

COMMENT ON TABLE item IS 'Server item crumbs';

COMMENT ON COLUMN item."ID" IS 'Unique item ID';
COMMENT ON COLUMN item."Name" IS 'Item name';
COMMENT ON COLUMN item."Type" IS 'Item clothing type';
COMMENT ON COLUMN item."Cost" IS 'Cost of item';
COMMENT ON COLUMN item."Member" IS 'Is member-only?';
COMMENT ON COLUMN item."Bait" IS 'Is bait item?';
COMMENT ON COLUMN item."Patched" IS 'Is item patched?';
COMMENT ON COLUMN item."EPF" IS 'Is EPF item?';
COMMENT ON COLUMN item."Tour" IS 'Gives tour status?';

DROP TABLE IF EXISTS igloo;
CREATE TABLE igloo (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL,
  "Cost" SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY("ID")
);

COMMENT ON TABLE igloo IS 'Server igloo crumbs';

COMMENT ON COLUMN igloo."ID" IS 'Unique igloo ID';
COMMENT ON COLUMN igloo."Name" IS 'Igloo name';
COMMENT ON COLUMN igloo."Cost" IS 'Cost of igloo';

DROP TABLE IF EXISTS location;
CREATE TABLE location (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL,
  "Cost" SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("ID")
);

COMMENT ON TABLE location IS 'Server location crumbs';

COMMENT ON COLUMN location."ID" IS 'Unique location ID';
COMMENT ON COLUMN location."Name" IS 'Location name';
COMMENT ON COLUMN location."Cost" IS 'Cost of location';

DROP TABLE IF EXISTS furniture;
CREATE TABLE furniture (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL,
  "Type" SMALLINT NOT NULL DEFAULT 1,
  "Sort" SMALLINT NOT NULL DEFAULT 1,
  "Cost" SMALLINT NOT NULL DEFAULT 0,
  "Member" BOOLEAN NOT NULL DEFAULT FALSE,
  "MaxQuantity" SMALLINT NOT NULL DEFAULT 100,
  PRIMARY KEY("ID")
);

COMMENT ON TABLE furniture IS 'Server furniture crumbs';

COMMENT ON COLUMN furniture."ID" IS 'Unique furniture ID';
COMMENT ON COLUMN furniture."Type" IS 'Furniture type ID';
COMMENT ON COLUMN furniture."Sort" IS 'Furniture sort ID';
COMMENT ON COLUMN furniture."Cost" IS 'Cost of furniture';
COMMENT ON COLUMN furniture."Member" IS 'Is member-only?';
COMMENT ON COLUMN furniture."MaxQuantity" IS 'Max inventory quantity';

DROP TABLE IF EXISTS flooring;
CREATE TABLE flooring (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30),
  "Cost" SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("ID")
);

COMMENT ON TABLE flooring IS 'Server flooring crumbs';

COMMENT ON COLUMN flooring."ID" IS 'Unique flooring ID';
COMMENT ON COLUMN flooring."Name" IS 'Flooring name';
COMMENT ON COLUMN flooring."Cost" IS 'Cost of flooring';

CREATE TYPE card_element AS ENUM ('s', 'w', 'f');
CREATE TYPE card_color AS ENUM ('b', 'g', 'o', 'p', 'r', 'y');

DROP TABLE IF EXISTS card;
CREATE TABLE card (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL,
  "SetID" SMALLINT NOT NULL DEFAULT 1,
  "PowerID" SMALLINT NOT NULL DEFAULT 0,
  "Element" card_element NOT NULL DEFAULT 's',
  "Color" card_color NOT NULL DEFAULT 'b',
  "Value" SMALLINT NOT NULL DEFAULT 2,
  "Description" VARCHAR(50) NOT NULL DEFAULT '',
  PRIMARY KEY ("ID")
);

COMMENT ON TABLE card IS 'Server jitsu card crumbs';

COMMENT ON COLUMN card."ID" IS 'Unique card ID';
COMMENT ON COLUMN card."Name" IS 'Card name';
COMMENT ON COLUMN card."SetID" IS 'Card set ID';
COMMENT ON COLUMN card."PowerID" IS 'Card power ID';
COMMENT ON COLUMN card."Element" IS 'Card element';
COMMENT ON COLUMN card."Color" IS 'Card color';
COMMENT ON COLUMN card."Value" IS 'Value of card';
COMMENT ON COLUMN card."Description" IS 'Play description';

DROP TABLE IF EXISTS room;
CREATE TABLE room (
  "ID" SMALLINT NOT NULL,
  "InternalID" SERIAL NOT NULL,
  "Name" VARCHAR(30) NOT NULL,
  "Member" BOOLEAN NOT NULL DEFAULT FALSE,
  "MaxUsers" SMALLINT NOT NULL DEFAULT 80,
  "RequiredItem" SMALLINT,
  PRIMARY KEY("ID", "InternalID"),
  CONSTRAINT room_ibfk_1 FOREIGN KEY ("RequiredItem") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE room IS 'Server room crumbs';

COMMENT ON COLUMN room."ID" IS 'Unique room ID';
COMMENT ON COLUMN room."InternalID" IS 'Internal room key';
COMMENT ON COLUMN room."Name" IS 'Room name';
COMMENT ON COLUMN room."Member" IS 'Is member-only?';
COMMENT ON COLUMN room."MaxUsers" IS 'Maximum room users';
COMMENT ON COLUMN room."RequiredItem" IS 'Required inventory item';

DROP TABLE IF EXISTS stamp;
CREATE TABLE stamp (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL,
  "GroupID" SMALLINT NOT NULL DEFAULT 0,
  "Member" BOOLEAN NOT NULL DEFAULT FALSE,
  "Rank" SMALLINT NOT NULL DEFAULT 1,
  "Description" VARCHAR(50) NOT NULL DEFAULT '',
  PRIMARY KEY("ID")
);

COMMENT ON TABLE stamp IS 'Server stamp crumbs';

COMMENT ON COLUMN stamp."ID" IS 'Unique stamp ID';
COMMENT ON COLUMN stamp."Name" IS 'Stamp name';
COMMENT ON COLUMN stamp."GroupID" IS 'Stamp group ID';
COMMENT ON COLUMN stamp."Member" IS 'Is member-only?';
COMMENT ON COLUMN stamp."Rank" IS 'Stamp difficulty ranking';
COMMENT ON COLUMN stamp."Description" IS 'Stamp description';

DROP TABLE IF EXISTS puffle_care_item;
CREATE TABLE puffle_care_item (
  "ID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL DEFAULT '',
  "Cost" SMALLINT NOT NULL DEFAULT 0,
  "Quantity" SMALLINT NOT NULL DEFAULT 1,
  "Member" BOOLEAN NOT NULL DEFAULT FALSE,
  "FoodEffect" SMALLINT NOT NULL DEFAULT 0,
  "RestEffect" SMALLINT NOT NULL DEFAULT 0,
  "PlayEffect" SMALLINT NOT NULL DEFAULT 0,
  "CleanEffect" SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("ID")
);

COMMENT ON TABLE puffle_care_item IS 'Server puffle care item crumbs';

COMMENT ON COLUMN puffle_care_item."ID" IS 'Unique care item ID';
COMMENT ON COLUMN puffle_care_item."Name" IS 'Care item name';
COMMENT ON COLUMN puffle_care_item."Cost" IS 'Cost of care item';
COMMENT ON COLUMN puffle_care_item."Quantity" IS 'Base quantity of purchase';
COMMENT ON COLUMN puffle_care_item."Member" IS 'Is member-only?';
COMMENT ON COLUMN puffle_care_item."FoodEffect" IS 'Effect on puffle food level';
COMMENT ON COLUMN puffle_care_item."RestEffect" IS 'Effect on puffle rest level';
COMMENT ON COLUMN puffle_care_item."PlayEffect" IS 'Effect on puffle play level';
COMMENT ON COLUMN puffle_care_item."CleanEffect" IS 'Effect on puffle clean level';

DROP TABLE IF EXISTS puffle;
CREATE TABLE puffle (
  "ID" SMALLINT NOT NULL,
  "ParentID" SMALLINT NOT NULL,
  "Name" VARCHAR(30) NOT NULL DEFAULT '',
  "Member" BOOLEAN NOT NULL DEFAULT FALSE,
  "FavouriteFood" SMALLINT NOT NULL,
  "RunawayPostcard" SMALLINT NOT NULL DEFAULT 100,
  "MaxFood" SMALLINT NOT NULL DEFAULT 100,
  "MaxRest" SMALLINT NOT NULL DEFAULT 100,
  "MaxClean" SMALLINT NOT NULL DEFAULT 100,
  PRIMARY KEY ("ID"),
  CONSTRAINT puffle_ibfk_1 FOREIGN KEY ("ParentID") REFERENCES puffle ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT puffle_ibfk_2 FOREIGN KEY ("FavouriteFood") REFERENCES puffle_care_item ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE puffle IS 'Server puffle crumbs';

COMMENT ON COLUMN puffle."ID" IS 'Unique puffle ID';
COMMENT ON COLUMN puffle."ParentID" IS 'Base color puffle ID';
COMMENT ON COLUMN puffle."Name" IS 'Puffle name';
COMMENT ON COLUMN puffle."Member" IS 'Is member-only?';
COMMENT ON COLUMN puffle."FavouriteFood" IS 'Favourite puffle-care item';
COMMENT ON COLUMN puffle."RunawayPostcard" IS 'Runaway postcard ID';
COMMENT ON COLUMN puffle."MaxFood" IS 'Maximum food level';
COMMENT ON COLUMN puffle."MaxRest" IS 'Maximum rest level';
COMMENT ON COLUMN puffle."MaxClean" IS 'Maximum clean level';

DROP TABLE IF EXISTS penguin;
CREATE TABLE penguin (
  "ID" SERIAL,
  "Username" VARCHAR(12) NOT NULL,
  "Nickname" VARCHAR(30) NOT NULL,
  "Approval" BOOLEAN NOT NULL DEFAULT FALSE,
  "Password" CHAR(255) NOT NULL,
  "LoginKey" CHAR(255) DEFAULT '',
  "Email" VARCHAR(255) NOT NULL,
  "RegistrationDate" TIMESTAMP NOT NULL,
  "Active" BOOLEAN NOT NULL DEFAULT FALSE,
  "LastPaycheck" TIMESTAMP NOT NULL,
  "MinutesPlayed" INT  NOT NULL DEFAULT 0,
  "Moderator" BOOLEAN NOT NULL DEFAULT FALSE,
  "Member" BOOLEAN NOT NULL DEFAULT TRUE,
  "MascotStamp" SMALLINT  DEFAULT NULL,
  "Coins" INT  NOT NULL DEFAULT 500,
  "Color" SMALLINT  DEFAULT NULL,
  "Head" SMALLINT  DEFAULT NULL,
  "Face" SMALLINT  DEFAULT NULL,
  "Neck" SMALLINT  DEFAULT NULL,
  "Body" SMALLINT  DEFAULT NULL,
  "Hand" SMALLINT  DEFAULT NULL,
  "Feet" SMALLINT  DEFAULT NULL,
  "Photo" SMALLINT  DEFAULT NULL,
  "Flag" SMALLINT  DEFAULT NULL,
  "Permaban" SMALLINT NOT NULL DEFAULT 0,
  "BookModified" SMALLINT NOT NULL DEFAULT 0,
  "BookColor" SMALLINT  NOT NULL DEFAULT 1,
  "BookHighlight" SMALLINT  NOT NULL DEFAULT 1,
  "BookPattern" SMALLINT  NOT NULL DEFAULT 0,
  "BookIcon" SMALLINT  NOT NULL DEFAULT 1,
  "AgentStatus" SMALLINT NOT NULL DEFAULT 0,
  "FieldOpStatus" SMALLINT NOT NULL DEFAULT 0,
  "CareerMedals" INT  NOT NULL DEFAULT 0,
  "AgentMedals" INT  NOT NULL DEFAULT 0,
  "LastFieldOp" TIMESTAMP NOT NULL,
  "NinjaRank" SMALLINT  NOT NULL DEFAULT 0,
  "NinjaProgress" SMALLINT  NOT NULL DEFAULT 0,
  "FireNinjaRank" SMALLINT  NOT NULL DEFAULT 0,
  "FireNinjaProgress" SMALLINT  NOT NULL DEFAULT 0,
  "WaterNinjaRank" SMALLINT  NOT NULL DEFAULT 0,
  "WaterNinjaProgress" SMALLINT  NOT NULL DEFAULT 0,
  "NinjaMatchesWon" INT  NOT NULL DEFAULT 0,
  "FireMatchesWon" INT  NOT NULL DEFAULT 0,
  "WaterMatchesWon" INT  NOT NULL DEFAULT 0,
  PRIMARY KEY ("ID"),
  CONSTRAINT penguin_ibfk_1 FOREIGN KEY ("Color") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_2 FOREIGN KEY ("Head") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_3 FOREIGN KEY ("Face") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_4 FOREIGN KEY ("Neck") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_5 FOREIGN KEY ("Body") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_6 FOREIGN KEY ("Hand") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_7 FOREIGN KEY ("Feet") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_8 FOREIGN KEY ("Photo") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_9 FOREIGN KEY ("Flag") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_ibfk_10 FOREIGN KEY ("MascotStamp") REFERENCES stamp ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "Email" ON Penguin("Email");
CREATE UNIQUE INDEX "Username" ON Penguin("Username");

ALTER TABLE penguin ALTER COLUMN "RegistrationDate" SET DEFAULT now();
ALTER TABLE penguin ALTER COLUMN "LastPaycheck" SET DEFAULT now();
ALTER TABLE penguin ALTER COLUMN "LastFieldOp" SET DEFAULT now();

COMMENT ON TABLE penguin IS 'Penguins';

COMMENT ON COLUMN penguin."ID" IS 'Unique penguin ID';
COMMENT ON COLUMN penguin."Username" IS 'Penguin login name';
COMMENT ON COLUMN penguin."Nickname" IS 'Penguin display name';
COMMENT ON COLUMN penguin."Approval" IS 'Username approval';
COMMENT ON COLUMN penguin."Password" IS 'Password hash';
COMMENT ON COLUMN penguin."LoginKey" IS 'Temporary login key';
COMMENT ON COLUMN penguin."Email" IS 'User Email address';
COMMENT ON COLUMN penguin."RegistrationDate" IS 'Date of registration';
COMMENT ON COLUMN penguin."Active" IS '"Email" activated';
COMMENT ON COLUMN penguin."LastPaycheck" IS 'EPF previous paycheck';
COMMENT ON COLUMN penguin."MinutesPlayed" IS 'Total minutes connected';
COMMENT ON COLUMN penguin."Moderator" IS 'Is user moderator?';
COMMENT ON COLUMN penguin."Member" IS 'Is user member?';
COMMENT ON COLUMN penguin."MascotStamp" IS 'Mascot stamp ID';
COMMENT ON COLUMN penguin."Coins" IS 'Penguin coins';
COMMENT ON COLUMN penguin."Color" IS 'Penguin color ID';
COMMENT ON COLUMN penguin."Head" IS 'Penguin head item ID';
COMMENT ON COLUMN penguin."Face" IS 'Penguin face item ID';
COMMENT ON COLUMN penguin."Neck" IS 'Penguin neck item ID';
COMMENT ON COLUMN penguin."Body" IS 'Penguin body item ID';
COMMENT ON COLUMN penguin."Hand" IS 'Penguin hand item ID';
COMMENT ON COLUMN penguin."Feet" IS 'Penguin feet item ID';
COMMENT ON COLUMN penguin."Photo" IS 'Penguin background ID';
COMMENT ON COLUMN penguin."Flag" IS 'Penguin pin ID';
COMMENT ON COLUMN penguin."Permaban" IS 'Is penguin banned forever?';
COMMENT ON COLUMN penguin."BookModified" IS 'Is book cover modified?';
COMMENT ON COLUMN penguin."BookColor" IS 'Stampbook cover color';
COMMENT ON COLUMN penguin."BookHighlight" IS 'Stampbook highlight color';
COMMENT ON COLUMN penguin."BookPattern" IS 'Stampbook cover pattern';
COMMENT ON COLUMN penguin."BookIcon" IS 'Stampbook cover icon';
COMMENT ON COLUMN penguin."AgentStatus" IS 'Is penguin EPF agent?';
COMMENT ON COLUMN penguin."FieldOpStatus" IS 'Is field op complete?';
COMMENT ON COLUMN penguin."CareerMedals" IS 'Total career medals';
COMMENT ON COLUMN penguin."AgentMedals" IS 'Current medals';
COMMENT ON COLUMN penguin."LastFieldOp" IS 'Date of last field op';
COMMENT ON COLUMN penguin."NinjaRank" IS 'Ninja rank';
COMMENT ON COLUMN penguin."NinjaProgress" IS 'Ninja progress';
COMMENT ON COLUMN penguin."FireNinjaRank" IS 'Fire ninja rank';
COMMENT ON COLUMN penguin."FireNinjaProgress" IS 'Fire ninja progress';
COMMENT ON COLUMN penguin."WaterNinjaRank" IS 'Water ninja rank';
COMMENT ON COLUMN penguin."WaterNinjaProgress" IS 'Water ninja progress';
COMMENT ON COLUMN penguin."NinjaMatchesWon" IS 'CardJitsu matches won';
COMMENT ON COLUMN penguin."FireMatchesWon" IS 'JitsuFire matches won';
COMMENT ON COLUMN penguin."WaterMatchesWon" IS 'JitsuWater matces won';


DROP TABLE IF EXISTS activation_key;
CREATE TABLE activation_key (
  "PenguinID" INT NOT NULL,
  "ActivationKey" CHAR(255) NOT NULL,
  PRIMARY KEY ("PenguinID", "ActivationKey")
);

COMMENT ON TABLE activation_key IS 'Penguin activation keys';

COMMENT ON COLUMN activation_key."PenguinID" IS 'Penguin ID';
COMMENT ON COLUMN activation_key."ActivationKey" IS 'Penguin activation key';

DROP TABLE IF EXISTS ban;
CREATE TABLE ban (
  "PenguinID" INT  NOT NULL,
  "Issued" TIMESTAMP NOT NULL,
  "Expires" TIMESTAMP NOT NULL,
  "ModeratorID" INT DEFAULT NULL,
  "Reason" SMALLINT NOT NULL,
  "Comment" text DEFAULT NULL,
  PRIMARY KEY ("PenguinID", "Issued", "Expires"),
  CONSTRAINT ban_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ban_ibfk_2 FOREIGN KEY ("ModeratorID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "ModeratorID" ON ban ("ModeratorID");

ALTER TABLE ban ALTER COLUMN "Issued" SET DEFAULT now();
ALTER TABLE ban ALTER COLUMN "Expires" SET DEFAULT now();

COMMENT ON TABLE ban IS 'Penguin ban records';

COMMENT ON COLUMN ban."PenguinID" IS 'Banned penguin ID';
COMMENT ON COLUMN ban."Issued" IS 'Issue date';
COMMENT ON COLUMN ban."Expires" IS 'Expiry date';
COMMENT ON COLUMN ban."ModeratorID" IS 'Moderator penguin ID';
COMMENT ON COLUMN ban."Reason" IS 'Ban reason';
COMMENT ON COLUMN ban."Comment" IS 'Ban comment';

DROP TABLE IF EXISTS buddy_list;
CREATE TABLE buddy_list (
  "PenguinID" INT  NOT NULL,
  "BuddyID" INT  NOT NULL,
  PRIMARY KEY ("PenguinID","BuddyID"),
  CONSTRAINT buddy_list_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT buddy_list_ibfk_2 FOREIGN KEY ("BuddyID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "BuddyID" ON buddy_list ("BuddyID");

COMMENT ON TABLE buddy_list IS 'Penguin buddy relationships';

DROP TABLE IF EXISTS buddy_request;
CREATE TABLE buddy_request (
  "PenguinID" INT NOT NULL,
  "RequesterID" INT NOT NULL,
  PRIMARY KEY ("PenguinID", "RequesterID"),
  CONSTRAINT buddy_request_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT buddy_request_ibfk_2 FOREIGN KEY ("RequesterID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE buddy_request IS 'Penguin buddy requests';

DROP TABLE IF EXISTS best_buddy;
CREATE TABLE best_buddy (
  "PenguinID" INT NOT NULL,
  "BuddyID" INT NOT NULL,
  PRIMARY KEY ("PenguinID", "BuddyID"),
  CONSTRAINT best_buddy_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT best_buddy_ibfk_2 FOREIGN KEY ("BuddyID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE best_buddy IS 'Penguin best buddies';

DROP TABLE IF EXISTS cover_stamps;
CREATE TABLE cover_stamps (
  "PenguinID" INT NOT NULL,
  "StampID" SMALLINT NOT NULL,
  "ItemID" SMALLINT NOT NULL,
  "X" SMALLINT NOT NULL DEFAULT 0,
  "Y" SMALLINT NOT NULL DEFAULT 0,
  "Type" SMALLINT NOT NULL DEFAULT 0,
  "Rotation" SMALLINT NOT NULL DEFAULT 0,
  "Depth" SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("PenguinID", "StampID"),
  CONSTRAINT cover_stamps_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT cover_stamps_ibfk_2 FOREIGN KEY ("StampID") REFERENCES stamp ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT cover_stamps_ibfk_3 FOREIGN KEY ("ItemID") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE cover_stamps IS 'Stamps placed on book cover';

COMMENT ON COLUMN cover_stamps."PenguinID" IS 'Unique penguin ID';
COMMENT ON COLUMN cover_stamps."StampID" IS 'Cover stamp or item ID';
COMMENT ON COLUMN cover_stamps."X" IS 'Cover X position';
COMMENT ON COLUMN cover_stamps."Y" IS 'Cover Y position';
COMMENT ON COLUMN cover_stamps."Type" IS 'Cover item type';
COMMENT ON COLUMN cover_stamps."Rotation" IS 'Stamp cover rotation';
COMMENT ON COLUMN cover_stamps."Depth" IS 'Stamp cover depth';

DROP TABLE IF EXISTS penguin_card;
CREATE TABLE penguin_card (
  "PenguinID" INT NOT NULL,
  "CardID" SMALLINT NOT NULL,
  "Quantity" SMALLINT NOT NULL DEFAULT 1,
  PRIMARY KEY ("PenguinID", "CardID"),
  CONSTRAINT penguin_card_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_card_ibfk_2 FOREIGN KEY ("CardID") REFERENCES card ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "PenguinID" ON penguin_card("PenguinID");

COMMENT ON TABLE penguin_card IS 'Penguin Card Jitsu decks';

COMMENT ON COLUMN penguin_card."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN penguin_card."CardID" IS 'Card type ID';
COMMENT ON COLUMN penguin_card."Quantity" IS 'Quantity owned';

DROP TABLE IF EXISTS penguin_furniture;
CREATE TABLE penguin_furniture (
  "PenguinID" INT  NOT NULL,
  "FurnitureID" SMALLINT  NOT NULL,
  "Quantity" SMALLINT  NOT NULL DEFAULT 1,
  PRIMARY KEY ("PenguinID", "FurnitureID"),
  CONSTRAINT penguin_furniture_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_furniture_ibfk_2 FOREIGN KEY ("FurnitureID") REFERENCES furniture ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE penguin_furniture IS 'Penguin owned furniture';

COMMENT ON COLUMN penguin_furniture."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN penguin_furniture."FurnitureID" IS 'Furniture item ID';
COMMENT ON COLUMN penguin_furniture."Quantity" IS 'Quantity owned';

DROP TABLE IF EXISTS penguin_igloo;
CREATE TABLE penguin_igloo (
  "ID" SERIAL,
  "PenguinID" INT NOT NULL,
  "Type" SMALLINT NOT NULL,
  "Flooring" SMALLINT NOT NULL DEFAULT 0,
  "Music" SMALLINT NOT NULL DEFAULT 0,
  "Locked" BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY ("ID"),
  CONSTRAINT igloo_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT igloo_ibfk_2 FOREIGN KEY ("Type") REFERENCES igloo ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT igloo_ibfk_3 FOREIGN KEY ("Flooring") REFERENCES flooring ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE penguin_igloo IS 'Penguin igloo settings';

COMMENT ON COLUMN penguin_igloo."ID" IS 'Unique igloo ID';
COMMENT ON COLUMN penguin_igloo."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN penguin_igloo."Type" IS 'Igloo type ID';
COMMENT ON COLUMN penguin_igloo."Floor" IS 'Igloo flooring ID';
COMMENT ON COLUMN penguin_igloo."Music" IS 'Igloo music ID';
COMMENT ON COLUMN penguin_igloo."Locked" IS 'Is igloo locked?';

DROP TABLE IF EXISTS igloo_like;
CREATE TABLE igloo_like (
  "IglooID" INT NOT NULL,
  "OwnerID" INT NOT NULL,
  "PlayerID" INT NOT NULL,
  "Count" SMALLiNT NOT NULL,
  "Date" DATE NOT NULL,
  PRIMARY KEY ("IglooID", "OwnerID", "PlayerID"),
  CONSTRAINT igloo_like_ibfk_1 FOREIGN KEY ("IglooID") REFERENCES penguin_igloo ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT igloo_like_ibfk_2 FOREIGN KEY ("OwnerID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT igloo_like_ibfk_3 FOREIGN KEY ("PlayerID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE igloo_like ALTER COLUMN "Date" SET DEFAULT now();

COMMENT ON TABLE igloo_like IS 'Player igloo likes';

COMMENT ON COLUMN igloo_like."IglooID" IS 'Igloo unique ID';
COMMENT ON COLUMN igloo_like."OwnerID" IS 'Owner unique ID';
COMMENT ON COLUMN igloo_like."PlayerID" IS 'Liker unique ID';
COMMENT ON COLUMN igloo_like."Count" IS 'Number of likes';
COMMENT ON COLUMN igloo_like."Date" IS 'Date of like';


DROP TABLE IF EXISTS penguin_location;
CREATE TABLE penguin_location (
  "PenguinID" INT NOT NULL,
  "LocationID" SMALLINT NOT NULL,
  PRIMARY KEY ("PenguinID", "LocationID"),
  CONSTRAINT penguin_location_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_location_ibfk_2 FOREIGN KEY ("LocationID") REFERENCES location ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE penguin_location IS 'Penguin owned locations';

COMMENT ON COLUMN penguin_location."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN penguin_location."LocationID" IS 'Location ID';

DROP TABLE IF EXISTS igloo_furniture;
CREATE TABLE igloo_furniture (
  "IglooID" INT  NOT NULL,
  "FurnitureID" SMALLINT  NOT NULL,
  "X" SMALLINT  NOT NULL DEFAULT 0,
  "Y" SMALLINT  NOT NULL DEFAULT 0,
  "Frame" SMALLINT  NOT NULL DEFAULT 0,
  "Rotation" SMALLINT  NOT NULL DEFAULT 0,
  PRIMARY KEY ("IglooID", "FurnitureID", "X", "Y", "Frame", "Rotation"),
  CONSTRAINT igloo_furniture_ibfk_1 FOREIGN KEY ("IglooID") REFERENCES penguin_igloo ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT igloo_furniture_ibfk_2 FOREIGN KEY ("FurnitureID") REFERENCES furniture ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IglooID ON igloo_furniture("IglooID");

COMMENT ON TABLE igloo_furniture IS 'Furniture placed inside igloos';

COMMENT ON COLUMN igloo_furniture."IglooID" IS 'Furniture igloo ID';
COMMENT ON COLUMN igloo_furniture."FurnitureID" IS 'Furniture item ID';
COMMENT ON COLUMN igloo_furniture."X" IS 'Igloo X position';
COMMENT ON COLUMN igloo_furniture."Y" IS 'Igloo Y position';
COMMENT ON COLUMN igloo_furniture."Frame" IS 'Furniture frame ID';
COMMENT ON COLUMN igloo_furniture."Rotation" IS 'Furniture rotation ID';

DROP TABLE IF EXISTS igloo_inventory;
CREATE TABLE igloo_inventory (
  "PenguinID" INT  NOT NULL DEFAULT 0,
  "IglooID" SMALLINT  NOT NULL,
  PRIMARY KEY ("PenguinID", "IglooID"),
  CONSTRAINT igloo_inventory_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT igloo_inventory_ibfk_2 FOREIGN KEY ("IglooID") REFERENCES igloo ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE igloo_inventory IS 'Penguin owned igloos';

COMMENT ON COLUMN igloo_inventory."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN igloo_inventory."IglooID" IS 'Igloo ID';

DROP TABLE IF EXISTS ignore_list;
CREATE TABLE ignore_list (
  "PenguinID" INT  NOT NULL,
  "IgnoreID" INT  NOT NULL,
  PRIMARY KEY ("PenguinID", "IgnoreID"),
  CONSTRAINT ignore_list_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT ignore_list_ibfk_2 FOREIGN KEY ("IgnoreID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IgnoreID ON ignore_list("IgnoreID");

COMMENT ON TABLE ignore_list IS 'Penguin ignore relationships';

DROP TABLE IF EXISTS penguin_item;
CREATE TABLE penguin_item (
  "PenguinID" INT  NOT NULL,
  "ItemID" SMALLINT  NOT NULL DEFAULT 0,
  PRIMARY KEY ("PenguinID", "ItemID"),
  CONSTRAINT penguin_item_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE penguin_item IS 'Penguin owned clothing items';

COMMENT ON COLUMN penguin_item."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN penguin_item."ItemID" IS 'Clothing item ID';

DROP TABLE IF EXISTS login;
CREATE TABLE login (
  "ID" SERIAL,
  "PenguinID" INT  NOT NULL,
  "Date" TIMESTAMP NOT NULL,
  "IPAddress" char(255) NOT NULL,
  PRIMARY KEY ("ID"),
  CONSTRAINT login_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE login ALTER COLUMN "Date" SET DEFAULT now();

COMMENT ON TABLE login IS 'Penguin login records';

COMMENT ON COLUMN login."ID" IS 'Unique login ID';
COMMENT ON COLUMN login."PenguinID" IS 'Login penguin ID';
COMMENT ON COLUMN login."Date" IS 'Login date';
COMMENT ON COLUMN login."IPAddress" IS 'Connection IP address';

DROP TABLE IF EXISTS postcard;
CREATE TABLE postcard (
  "ID" SERIAL,
  "SenderID" INT  DEFAULT NULL,
  "RecipientID" INT  NOT NULL,
  "Type" SMALLINT  NOT NULL,
  "SendDate" TIMESTAMP NOT NULL,
  "Details" char(255) NOT NULL DEFAULT '',
  "HasRead" BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY ("ID"),
  CONSTRAINT postcard_ibfk_1 FOREIGN KEY ("SenderID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT postcard_ibfk_2 FOREIGN KEY ("RecipientID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE postcard ALTER COLUMN "SendDate" SET DEFAULT now();

CREATE INDEX "SenderID" ON postcard("SenderID");
CREATE INDEX "RecipientID" ON postcard("RecipientID");

COMMENT ON TABLE postcard IS 'Sent postcards';

COMMENT ON COLUMN postcard."ID" IS 'Unique postcard ID';
COMMENT ON COLUMN postcard."SenderID" IS 'Sender penguin ID';
COMMENT ON COLUMN postcard."RecipientID" IS 'Postcard type ID';
COMMENT ON COLUMN postcard."Type" IS 'Postcard type ID';
COMMENT ON COLUMN postcard."SendDate" IS 'Postcard type ID';
COMMENT ON COLUMN postcard."Details" IS 'Postcard details';
COMMENT ON COLUMN postcard."HasRead" IS 'Is read?';

DROP TABLE IF EXISTS penguin_puffle;
CREATE TABLE penguin_puffle (
  "ID" SERIAL,
  "PenguinID" INT NOT NULL,
  "Name" varchar(16) NOT NULL,
  "AdoptionDate" TIMESTAMP NOT NULL,
  "Type" SMALLINT NOT NULL,
  "Food" SMALLINT NOT NULL DEFAULT 100,
  "Play" SMALLINT NOT NULL DEFAULT 100,
  "Rest" SMALLINT NOT NULL DEFAULT 100,
  "Clean" SMALLINT NOT NULL DEFAULT 100,
  "Walking" BOOLEAN DEFAULT FALSE,
  "Hat" SMALLINT NOT NULL,
  "Backyard" BOOLEAN DEFAULT FALSE,
  "HasDug" BOOLEAN DEFAULT FALSE,
  PRIMARY KEY ("ID"),
  CONSTRAINT penguin_puffle_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_puffle_ibfk_2 FOREIGN KEY ("Type") REFERENCES puffle ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_puffle_ibfk_3 FOREIGN KEY ("Hat") REFERENCES puffle_care_item ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE penguin_puffle ALTER COLUMN "AdoptionDate" SET DEFAULT now();

COMMENT ON TABLE penguin_puffle IS 'Adopted puffles';

COMMENT ON COLUMN penguin_puffle."ID" IS 'Unique puffle ID';
COMMENT ON COLUMN penguin_puffle."PenguinID" IS 'Owner penguin ID';
COMMENT ON COLUMN penguin_puffle."Name" IS 'Puffle name';
COMMENT ON COLUMN penguin_puffle."AdoptionDate" IS 'Date of adoption';
COMMENT ON COLUMN penguin_puffle."Type" IS 'Puffle type ID';
COMMENT ON COLUMN penguin_puffle."Food" IS 'Puffle health %';
COMMENT ON COLUMN penguin_puffle."Play" IS 'Puffle hunger %';
COMMENT ON COLUMN penguin_puffle."Rest" IS 'Puffle rest %';
COMMENT ON COLUMN penguin_puffle."Clean" IS 'Puffle clean %';
COMMENT ON COLUMN penguin_puffle."Walking" IS 'Is being walked?';
COMMENT ON COLUMN penguin_puffle."Hat" IS 'Puffle hat item ID';
COMMENT ON COLUMN penguin_puffle."Backyard" IS 'Is in backyard?';
COMMENT ON COLUMN penguin_puffle."HasDug" IS 'Has dug?';

DROP TABLE IF EXISTS puffle_quest;
CREATE TABLE puffle_quest (
  "PenguinID" SMALLINT NOT NULL,
  "TaskID" SMALLINT NOT NULL,
  "CompletionDate" TIMESTAMP DEFAULT NULL,
  "ItemCollected" BOOLEAN NOT NULL DEFAULT FALSE,
  "CoinsCollected" BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY ("PenguinID", "TaskID"),
  CONSTRAINT puffle_quest_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE puffle_quest IS 'Puffle quest progress';

COMMENT ON COLUMN puffle_quest."PenguinID" IS 'Quest penguin ID';
COMMENT ON COLUMN puffle_quest."TaskID" IS 'Quest task ID';
COMMENT ON COLUMN puffle_quest."CompletionDate" IS 'Time of completion';
COMMENT ON COLUMN puffle_quest."ItemCollected" IS 'Item collection status';
COMMENT ON COLUMN puffle_quest."CoinsCollected" IS 'Coins collection status';

CREATE TYPE redemption_type AS ENUM ('DS','BLANKET','CARD','GOLDEN','CAMPAIGN');

DROP TABLE IF EXISTS redemption_code;
CREATE TABLE redemption_code (
  "ID" SERIAL,
  "Code" varchar(16) NOT NULL,
  "Type" redemption_type NOT NULL DEFAULT 'BLANKET',
  "Coins" INT  NOT NULL DEFAULT 0,
  "Expires" TIMESTAMP DEFAULT NULL,
  PRIMARY KEY ("ID")
);

COMMENT ON TABLE redemption_code IS 'Redemption codes';

COMMENT ON COLUMN redemption_code."ID" IS 'Unique code ID';
COMMENT ON COLUMN redemption_code."Code" IS 'Redemption code';
COMMENT ON COLUMN redemption_code."Type" IS 'Code type';
COMMENT ON COLUMN redemption_code."Coins" IS 'Code coins amount';
COMMENT ON COLUMN redemption_code."Expires" IS 'Expiry date';

DROP TABLE IF EXISTS penguin_redemption;
CREATE TABLE penguin_redemption (
  "PenguinID" INT  NOT NULL DEFAULT 0,
  "CodeID" INT  NOT NULL DEFAULT 0,
  PRIMARY KEY ("PenguinID", "CodeID"),
  CONSTRAINT penguin_redemption_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT penguin_redemption_ibfk_2 FOREIGN KEY ("CodeID") REFERENCES redemption_code ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "CodeID" ON penguin_redemption("CodeID");

COMMENT ON TABLE penguin_redemption IS 'Redeemed codes';

COMMENT ON COLUMN penguin_redemption."PenguinID" IS 'Unique penguin ID';
COMMENT ON COLUMN penguin_redemption."CodeID" IS 'Unique code ID';


DROP TABLE IF EXISTS redemption_award;
CREATE TABLE redemption_award (
  "CodeID" INT  NOT NULL DEFAULT 0,
  "CardID" SMALLINT DEFAULT NULL,
  "ItemID" SMALLINT DEFAULT NULL,
  PRIMARY KEY ("CodeID", "CardID", "ItemID"),
  CONSTRAINT redemption_award_ibfk_1 FOREIGN KEY ("CodeID") REFERENCES redemption_code ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT redemption_award_ibfk_2 FOREIGN KEY ("CardID") REFERENCES card ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT redemption_award_ibfk_3 FOREIGN KEY ("ItemID") REFERENCES item ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE redemption_award IS 'Redemption code awards';

COMMENT ON COLUMN redemption_award."CodeID" IS 'Unique code ID';
COMMENT ON COLUMN redemption_award."CardID" IS 'Code card ID';
COMMENT ON COLUMN redemption_award."ItemID" IS 'Code item ID';

DROP TABLE IF EXISTS penguin_stamp;
CREATE TABLE penguin_stamp (
  "PenguinID" INT  NOT NULL,
  "StampID" SMALLINT  NOT NULL,
  "Recent" BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY ("PenguinID", "StampID"),
  CONSTRAINT stamp_ibfk_1 FOREIGN KEY ("PenguinID") REFERENCES penguin ("ID") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT stamp_ibfk_2 FOREIGN KEY ("StampID") REFERENCES stamp ("ID") ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE penguin_stamp IS 'Penguin earned stamps';

COMMENT ON COLUMN penguin_stamp."PenguinID" IS 'Stamp penguin ID';
COMMENT ON COLUMN penguin_stamp."StampID" IS 'Stamp ID';
COMMENT ON COLUMN penguin_stamp."Recent" IS 'Is recently earned?';
