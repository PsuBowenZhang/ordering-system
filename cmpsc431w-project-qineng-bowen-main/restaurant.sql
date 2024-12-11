DROP DATABASE IF EXISTS `restaurant`;

CREATE DATABASE `restaurant`;

USE `restaurant`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for bill
-- ----------------------------
DROP TABLE IF EXISTS `bill`;
CREATE TABLE `bill`  (
  `BillID` int NOT NULL AUTO_INCREMENT,
  `OrderID` int NOT NULL,
  `DiscountID` int NOT NULL,
  `DiscountAmount` decimal(6, 2) NULL DEFAULT 0.00,
  `TaxID` int NOT NULL,
  `TaxAmount` decimal(6, 2) NULL DEFAULT 0.00,
  `TipAmount` decimal(6, 2) NULL DEFAULT NULL,
  `BillTotalAmount` decimal(10, 2) NULL DEFAULT NULL,
  PRIMARY KEY (`BillID`) USING BTREE,
  UNIQUE INDEX `OrderID`(`OrderID` ASC) USING BTREE,
  INDEX `bill_ibfk_2`(`DiscountID` ASC) USING BTREE,
  INDEX `bill_ibfk_3`(`TaxID` ASC) USING BTREE,
  CONSTRAINT `bill_ibfk_1` FOREIGN KEY (`OrderID`) REFERENCES `orders` (`OrderID`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `bill_ibfk_2` FOREIGN KEY (`DiscountID`) REFERENCES `discount` (`DiscountID`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `bill_ibfk_3` FOREIGN KEY (`TaxID`) REFERENCES `tax` (`TaxID`) ON DELETE RESTRICT ON UPDATE RESTRICT
);

-- ----------------------------
-- Records of bill
-- ----------------------------
INSERT INTO `bill` VALUES (1, 12, 1, 0.00, 1, 0.00, 22.00, 30.48);
INSERT INTO `bill` VALUES (2, 14, 1, 0.00, 1, 0.00, 1.00, 18.98);
INSERT INTO `bill` VALUES (3, 13, 3, 0.50, 1, 0.00, 10.00, 14.48);
INSERT INTO `bill` VALUES (4, 8, 4, 5.24, 4, 5.94, 5.00, 40.66);
INSERT INTO `bill` VALUES (5, 7, 4, 3.75, 3, 2.12, 3.00, 26.35);
INSERT INTO `bill` VALUES (6, 6, 3, 2.60, 2, 1.17, 2.00, 26.54);
INSERT INTO `bill` VALUES (7, 1, 3, 2.60, 3, 2.34, NULL, NULL);

-- ----------------------------
-- Table structure for categories
-- ----------------------------
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories`  (
  `CateID` int NOT NULL AUTO_INCREMENT,
  `CateName` varchar(20),
  `ParentID` int NULL DEFAULT NULL,
  PRIMARY KEY (`CateID`) USING BTREE,
  INDEX `ParentID`(`ParentID` ASC) USING BTREE,
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`ParentID`) REFERENCES `categories` (`CateID`) ON DELETE CASCADE ON UPDATE RESTRICT
);

-- ----------------------------
-- Records of categories
-- ----------------------------
INSERT INTO `categories` VALUES (1, 'Main Courses', NULL);
INSERT INTO `categories` VALUES (2, 'Desserts', NULL);
INSERT INTO `categories` VALUES (3, 'Beverages', NULL);
INSERT INTO `categories` VALUES (4, 'Seafood', 1);
INSERT INTO `categories` VALUES (5, 'Pizza', 1);
INSERT INTO `categories` VALUES (6, 'Burger', 1);
INSERT INTO `categories` VALUES (7, 'Ice Cream', 2);
INSERT INTO `categories` VALUES (8, 'Cake', 2);
INSERT INTO `categories` VALUES (9, 'Fruit Tart', 2);
INSERT INTO `categories` VALUES (10, 'Coffee', 3);
INSERT INTO `categories` VALUES (11, 'Juice', 3);

-- ----------------------------
-- Table structure for discount
-- ----------------------------
DROP TABLE IF EXISTS `discount`;
CREATE TABLE `discount`  (
  `DiscountID` int NOT NULL AUTO_INCREMENT,
  `DiscountName` varchar(50),
  `DiscountPercent` decimal(5, 2) NOT NULL,
  PRIMARY KEY (`DiscountID`) USING BTREE,
  CONSTRAINT `discount_chk_1` CHECK ((`DiscountPercent` >= 0.0) and (`DiscountPercent` <= 100.0))
);

-- ----------------------------
-- Records of discount
-- ----------------------------
INSERT INTO `discount` VALUES (1, 'No', 0.00);
INSERT INTO `discount` VALUES (2, 'General', 5.00);
INSERT INTO `discount` VALUES (3, 'Holiday', 10.00);
INSERT INTO `discount` VALUES (4, 'Employee', 15.00);

-- ----------------------------
-- Table structure for menuitem
-- ----------------------------
DROP TABLE IF EXISTS `menuitem`;
CREATE TABLE `menuitem`  (
  `ItemID` int NOT NULL AUTO_INCREMENT,
  `ItemName` varchar(50) NOT NULL,
  `ItemImage` varchar(255) NULL DEFAULT NULL,
  `Price` decimal(6, 2) NOT NULL,
  `Description` varchar(255) NULL DEFAULT NULL,
  `Stock` int NOT NULL,
  `CateID` int NOT NULL,
  `CreateTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ItemID`) USING BTREE,
  INDEX `CateID`(`CateID` ASC) USING BTREE,
  CONSTRAINT `menuitem_ibfk_1` FOREIGN KEY (`CateID`) REFERENCES `categories` (`CateID`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `menuitem_chk_1` CHECK (`Stock` >= 0)
);

-- ----------------------------
-- Records of menuitem
-- ----------------------------
INSERT INTO `menuitem` VALUES (2, 'Grilled Salmon', 'static/uploads/GrilledSalmon_1733125624.webp', 12.99, 'Freshly grilled salmon with lemon.', 4, 4, '2024-11-27 13:35:00');
INSERT INTO `menuitem` VALUES (3, 'Shrimp Scampi', 'static/uploads/ShrimpScampi_1733122820.webp', 10.99, 'Delicious shrimp in garlic butter sauce.', 4, 4, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (4, 'Lobster Roll', 'static/uploads/Lobster_Roll_1733122939.png', 14.99, 'Classic lobster roll with herbs.', 34, 4, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (5, 'Crab Cakes', 'static/uploads/CrabCakes_1733122996.jpg', 9.99, 'Golden fried crab cakes.', 27, 4, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (6, 'Margherita Pizza', 'static/uploads/MargheritaPizza_1733123243.jpg', 8.99, 'Classic pizza with tomato and mozzarella.', 79, 5, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (7, 'Pepperoni Pizza', 'static/uploads/PepperoniPizza_1733123254.webp', 9.49, 'Cheesy pizza topped with pepperoni slices.', 88, 5, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (8, 'Veggie Pizza', 'static/uploads/VeggiePizza_1733123458.webp', 8.49, 'Pizza loaded with fresh vegetables.', 68, 5, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (9, 'BBQ Chicken Pizza', 'static/uploads/BBQChickenPizza_1733123263.jpg', 10.49, 'BBQ chicken topped pizza.', 59, 5, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (10, 'Cheeseburger', 'static/uploads/Cheeseburger_1733123320.jpg', 5.49, 'Classic cheeseburger with pickles.', 119, 6, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (11, 'Double Cheeseburger', 'static/uploads/DoubleCheeseburger_1733123431.webp', 6.99, 'Double layers of cheese and beef.', 0, 6, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (13, 'Veggie Burger', 'static/uploads/VeggieBurger_1733123564.webp', 5.99, 'Healthy veggie patty burger.', 80, 6, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (14, 'Vanilla Cone', 'static/uploads/VanillaCone_1733123714.webp', 1.49, 'Soft serve vanilla cone.', 150, 7, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (15, 'Chocolate Sundae', 'static/uploads/ChocolateSundae_1733123768.webp', 2.49, 'Creamy sundae with chocolate topping.', 0, 7, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (16, 'Strawberry Sundae', 'static/uploads/StrawberrySundae_1733123861.webp', 2.49, 'Creamy sundae with strawberry topping.', 100, 7, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (17, 'Oreo McFlurry', 'static/uploads/OreoMcFlurry_1733123851.webp', 3.49, 'Vanilla soft serve with Oreo pieces.', 90, 7, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (18, 'Chocolate Cake', 'static/uploads/ChocolateCake_1733124076.webp', 3.99, 'Rich chocolate cake slice.', 58, 8, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (19, 'Cheesecake', 'static/uploads/Cheesecake_1733124175.jpg', 4.49, 'Creamy New York style cheesecake.', 48, 8, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (20, 'Carrot Cake', 'static/uploads/CarrotCake_1733124257.webp', 3.99, 'Moist cake with cream cheese frosting.', 20, 8, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (22, 'Strawberry Tart', 'static/uploads/StrawberryTart_1733125562.webp', 3.99, 'Fresh strawberries on a tart crust.', 70, 9, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (23, 'Mixed Berry Tart', 'static/uploads/MixedBerryTart_1733125576.jpg', 4.49, 'Tart topped with assorted berries.', 60, 9, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (26, 'Espresso', 'static/uploads/Espresso_1733125585.webp', 1.99, 'Rich and bold espresso shot.', 200, 10, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (27, 'Latte', 'static/uploads/Latte_1733125594.webp', 2.99, 'Creamy latte with steamed milk.', 180, 10, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (30, 'Orange Juice', 'static/uploads/OrangeJuice_1733125603.webp', 2.49, 'Freshly squeezed orange juice.', 148, 11, '2024-11-27 23:35:00');
INSERT INTO `menuitem` VALUES (31, 'Apple Juice', 'static/uploads/AppleJuice_1733125611.webp', 2.49, 'Freshly chilled apple juice.', 139, 11, '2024-11-27 23:35:00');

-- ----------------------------
-- Table structure for orderdetail
-- ----------------------------
DROP TABLE IF EXISTS `orderdetail`;
CREATE TABLE `orderdetail`  (
  `OrderDetailID` int NOT NULL AUTO_INCREMENT,
  `OrderID` int NOT NULL,
  `ItemID` int NOT NULL,
  `Quantity` int NOT NULL,
  `IsLike` tinyint(1) NULL DEFAULT NULL,
  PRIMARY KEY (`OrderDetailID`) USING BTREE,
  INDEX `OrderID`(`OrderID` ASC) USING BTREE,
  INDEX `ItemID`(`ItemID` ASC) USING BTREE,
  CONSTRAINT `orderdetail_ibfk_1` FOREIGN KEY (`OrderID`) REFERENCES `orders` (`OrderID`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `orderdetail_ibfk_2` FOREIGN KEY (`ItemID`) REFERENCES `menuitem` (`ItemID`) ON DELETE CASCADE ON UPDATE RESTRICT
);

-- ----------------------------
-- Records of orderdetail
-- ----------------------------
INSERT INTO `orderdetail` VALUES (1, 1, 3, 1, NULL);
INSERT INTO `orderdetail` VALUES (2, 1, 4, 1, NULL);
INSERT INTO `orderdetail` VALUES (3, 3, 4, 2, NULL);
INSERT INTO `orderdetail` VALUES (4, 3, 5, 1, NULL);
INSERT INTO `orderdetail` VALUES (5, 3, 7, 1, NULL);
INSERT INTO `orderdetail` VALUES (6, 4, 3, 1, 1);
INSERT INTO `orderdetail` VALUES (7, 4, 4, 1, 0);
INSERT INTO `orderdetail` VALUES (8, 5, 3, 1, NULL);
INSERT INTO `orderdetail` VALUES (9, 6, 30, 1, 1);
INSERT INTO `orderdetail` VALUES (10, 6, 4, 1, 1);
INSERT INTO `orderdetail` VALUES (11, 6, 8, 1, 1);
INSERT INTO `orderdetail` VALUES (12, 7, 4, 1, 1);
INSERT INTO `orderdetail` VALUES (13, 7, 5, 1, 1);
INSERT INTO `orderdetail` VALUES (14, 8, 10, 1, 1);
INSERT INTO `orderdetail` VALUES (15, 8, 5, 1, 1);
INSERT INTO `orderdetail` VALUES (16, 8, 6, 1, 1);
INSERT INTO `orderdetail` VALUES (17, 8, 9, 1, 1);
INSERT INTO `orderdetail` VALUES (21, 12, 18, 1, 1);
INSERT INTO `orderdetail` VALUES (22, 12, 19, 1, 1);
INSERT INTO `orderdetail` VALUES (23, 13, 30, 1, NULL);
INSERT INTO `orderdetail` VALUES (24, 13, 31, 1, NULL);
INSERT INTO `orderdetail` VALUES (25, 14, 7, 1, 1);
INSERT INTO `orderdetail` VALUES (26, 14, 8, 1, 1);
INSERT INTO `orderdetail` VALUES (27, 15, 18, 1, NULL);
INSERT INTO `orderdetail` VALUES (28, 15, 19, 1, NULL);
INSERT INTO `orderdetail` VALUES (29, 15, 20, 20, NULL);

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders`  (
  `OrderID` int NOT NULL AUTO_INCREMENT,
  `UserID` int NOT NULL,
  `OrderTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `OrderAmount` decimal(8, 2) NULL DEFAULT NULL,
  `OrderStatus` enum('Waiting','Confirmed','Completed','Paid') NOT NULL DEFAULT 'Waiting',
  PRIMARY KEY (`OrderID`) USING BTREE,
  INDEX `UserID`(`UserID` ASC) USING BTREE,
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`UserID`) REFERENCES `users` (`UserID`) ON DELETE CASCADE ON UPDATE RESTRICT
);

-- ----------------------------
-- Records of orders
-- ----------------------------
INSERT INTO `orders` VALUES (1, 5, '2024-11-29 21:18:45', 25.98, 'Completed');
INSERT INTO `orders` VALUES (3, 5, '2024-11-29 22:24:44', 49.46, 'Confirmed');
INSERT INTO `orders` VALUES (4, 10, '2024-11-29 23:02:30', 25.98, 'Confirmed');
INSERT INTO `orders` VALUES (5, 10, '2024-12-03 00:29:28', 10.99, 'Confirmed');
INSERT INTO `orders` VALUES (6, 10, '2024-12-03 18:42:36', 25.97, 'Paid');
INSERT INTO `orders` VALUES (7, 10, '2024-12-03 18:44:14', 24.98, 'Paid');
INSERT INTO `orders` VALUES (8, 10, '2024-12-03 18:48:27', 34.96, 'Paid');
INSERT INTO `orders` VALUES (12, 10, '2024-12-05 19:05:53', 8.48, 'Paid');
INSERT INTO `orders` VALUES (13, 10, '2024-12-05 07:54:49', 4.98, 'Paid');
INSERT INTO `orders` VALUES (14, 10, '2024-12-05 08:36:53', 17.98, 'Paid');
INSERT INTO `orders` VALUES (15, 10, '2024-12-06 02:25:35', 88.28, 'Confirmed');

-- ----------------------------
-- Table structure for tax
-- ----------------------------
DROP TABLE IF EXISTS `tax`;
CREATE TABLE `tax`  (
  `TaxID` int NOT NULL AUTO_INCREMENT,
  `TaxName` varchar(50) NOT NULL,
  `TaxPercent` decimal(5, 2) NOT NULL,
  PRIMARY KEY (`TaxID`) USING BTREE,
  CONSTRAINT `tax_chk_1` CHECK ((`TaxPercent` >= 0.0) and (`TaxPercent` <= 100.0))
);

-- ----------------------------
-- Records of tax
-- ----------------------------
INSERT INTO `tax` VALUES (1, 'No', 0.00);
INSERT INTO `tax` VALUES (2, 'Low', 5.00);
INSERT INTO `tax` VALUES (3, 'Normal', 10.00);
INSERT INTO `tax` VALUES (4, 'High', 20.00);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `UserID` int NOT NULL AUTO_INCREMENT,
  `UserName` varchar(50) NOT NULL,
  `Role` enum('Customer','Manager') NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `IsActive` tinyint(1) NULL DEFAULT 1,
  PRIMARY KEY (`UserID`) USING BTREE,
  UNIQUE INDEX `Email`(`Email` ASC) USING BTREE
);

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (4, 'Administrator', 'Manager', 'admin@mail.com', 'pbkdf2:sha256:1000000$DrG9d2b7EWPFnOoJ$ddafbb81625949d02aeeab9c6f081fd259d720afba6f8b85c36b6cef12179a55', 1);
INSERT INTO `users` VALUES (5, 'Tomas Blues', 'Customer', 'tomas@gmail.com', 'scrypt:32768:8:1$cW26iKtRj7esWFx9$f469c312c291330b026c14fb562e0b89ea04b2225e2ba3d70518a053c2e1d399490fed8f57acf9494c7e49ec1518f5713d2e65f8e25ee4de8d519fd23e247751', 1);
INSERT INTO `users` VALUES (8, 'test admin', 'Manager', 'test@admin.com', 'scrypt:32768:8:1$2jTJNDcHX4rLgETn$1984748fef09f8980b448504308b12a135fe6cd5b2b8dafda582b64b0ba8948a6add30fae598bd482d7787b6e4e73b453b215ec54421d6db19a16cb907b213eb', 1);
INSERT INTO `users` VALUES (9, 'test customer', 'Customer', 'test@customer.com', 'scrypt:32768:8:1$7PSbGj3PJwTXXB63$b7ecb1e2d4557a2646da131c3502631c0f5239d447291288c5798015ae44593bb4cf16899e18552b79691b77b11715d08c0594fd2dd9b81c65ff237917dcee40', 0);
INSERT INTO `users` VALUES (10, 'admin@email.com', 'Customer', 'admin@email.com', 'scrypt:32768:8:1$a4g87RtEO7siqjRS$056123282afbc203d3c37370744583ec2698176a8cf88971da0369066cb492d4bdbb38db29926492ac278144231f522aba6e90ddbf6cb86d1fb9b003424e3f1d', 1);

SET FOREIGN_KEY_CHECKS = 1;
