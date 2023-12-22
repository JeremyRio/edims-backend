import express from "express";
import { Request, Response } from "express";
import { PrismaClient } from "@prisma/client";
import { verifyToken } from "../authentication/authentication";
import { Storage } from "@google-cloud/storage";
import multer from "multer";

const prisma = new PrismaClient();
const storage = new Storage({
  keyFilename: "./service-account.json",
});
const bucket = storage.bucket("edims-item");
const upload = multer({ storage: multer.memoryStorage() });
const router = express.Router();

/**
 * @swagger
 * tags:
 *   name: Item
 *   description: Item management
 */

/**
 * @swagger
 * /item/all:
 *   get:
 *     tags: [Item]
 *     summary: Retrieve all items
 *     description: Fetches all items for the authenticated user.
 *     responses:
 *       200:
 *         description: List of items
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Item'
 *       500:
 *         description: Internal server error
 */

router.get("/all", verifyToken, async (req: Request, res: Response) => {
  try {
    const user = (req as any).user;
    const items = await prisma.item.findMany({
      where: {
        userid: user.user.id,
      },
    });
    res.status(200).json({ message: "Item retrieve success", items: items });
  } catch (error) {
    console.error(error);
    res.status(500).send({ message: "Internal server error" });
  }
});

/**
 * @swagger
 * /item:
 *   post:
 *     tags: [Item]
 *     summary: Create a new item
 *     description: Adds a new item with an image, name, category, and date.
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               name:
 *                 type: string
 *               category:
 *                 type: string
 *               date:
 *                 type: string
 *               image:
 *                 type: string
 *                 format: binary
 *     responses:
 *       201:
 *         description: Item successfully created
 *       400:
 *         description: Invalid input
 *       500:
 *         description: Internal server error
 */

router.post(
  "/",
  verifyToken,
  upload.single("image"),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const { name, category, date } = req.body;
      const file = req.file;

      if (!date || !file || !name || !category) {
        return res.status(400).send({ message: "All fields are required." });
      }

      const bucketfilename = `${user.user.id}/items/${Date.now()}-${
        file.originalname
      }`;

      const blob = bucket.file(bucketfilename);
      const blobStream = blob.createWriteStream({
        metadata: {
          contentType: file.mimetype,
        },
        resumable: false,
      });

      blobStream.on("error", (err) => {
        console.error(err);
        return res
          .status(500)
          .send({ message: "Error uploading to Google Cloud Storage" });
      });

      blobStream.on("finish", async () => {
        const publicUrl = `https://storage.googleapis.com/${bucket.name}/${blob.name}`;

        const newItem = await prisma.item.create({
          data: {
            userid: user.user.id,
            name: name,
            image: publicUrl,
            category: category,
            date: date,
          },
        });
        res
          .status(201)
          .json({ message: "Item successfully created", item: newItem });
      });

      blobStream.end(file.buffer);
    } catch (error) {
      console.error(error);
      res.status(500).send({ message: "Internal server error" });
    }
  }
);

/**
 * @swagger
 * /item/{id}:
 *   delete:
 *     tags: [Item]
 *     summary: Delete an item
 *     description: Deletes an item by ID.
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         description: Item ID
 *     responses:
 *       200:
 *         description: Item deleted successfully
 *       401:
 *         description: Unauthorized deletion
 *       404:
 *         description: Item not found
 *       500:
 *         description: Internal server error
 */

router.delete("/:id", verifyToken, async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const user = (req as any).user;
    // Convert the id to a number and validate
    const itemId = parseInt(id);
    if (isNaN(itemId)) {
      return res.status(400).json({ message: "Invalid item ID" });
    }

    const item = await prisma.item.findUnique({
      where: { id: itemId },
    });

    // Check if item exist
    if (!item) {
      return res.status(404).json({ message: "Item not found" });
    }

    // Check if the item is user's
    if (item.userid !== user.user.id) {
      return res.status(401).json({ message: "Unauthorized deletion" });
    }

    // Delete the item from the database
    const deletedItem = await prisma.item.delete({
      where: { id: itemId },
    });

    // If the item is successfully deleted
    if (deletedItem) {
      res.status(200).json({ message: "Item deleted successfully" });
    } else {
      res.status(404).json({ message: "Item not found" });
    }
  } catch (error) {
    // Handle any errors that occur during deletion
    console.error(error);
    res.status(500).json({ message: "Error deleting item" });
  }
});

export default router;
