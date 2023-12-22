import express, { Request, Response } from "express";
import { Item, User, LoginCredentials, UserWithoutPassword } from "./interface";
import bcrypt from "bcrypt";
import { PrismaClient } from "@prisma/client";
import { generateToken, verifyToken } from "./authentication";
import { Storage } from "@google-cloud/storage";
import dotenv from "dotenv";
import multer from "multer";

dotenv.config();

const app = express();
const port = process.env.port || 8080;
const prisma = new PrismaClient();
const storage = new Storage({
  keyFilename: "./service-account.json",
});
const bucket = storage.bucket("edims-item");
const upload = multer({ storage: multer.memoryStorage() });

app.use(express.json());

app.get("/", (req, res) => {
  res.send("Hello, TypeScript Express!");
});

app.post("/register", async (req: Request, res: Response) => {
  try {
    const { email, username, password }: User = req.body;

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    const newUser = await prisma.user.create({
      data: {
        email,
        username,
        password: hashedPassword,
      },
    });
    const { password: _, ...userWithoutPassword } = newUser;
    res
      .status(201)
      .json({ message: "Register success", user: userWithoutPassword });
  } catch (error) {
    res.status(400).json({ message: "Unable to register user" });
  }
});

app.post("/login", async (req: Request, res: Response) => {
  try {
    const { email, password }: LoginCredentials = req.body;
    const user = await prisma.user.findUnique({ where: { email } });

    if (user && bcrypt.compareSync(password, user.password)) {
      const { password: _, ...userWithoutPassword } = user;
      const token = generateToken(userWithoutPassword);
      res.status(200).json({
        message: "Login successful",
        user: userWithoutPassword,
        token: token,
      });
    } else {
      res.status(401).json({ message: "Invalid email or password" });
    }
  } catch (error) {
    res.status(500).json({ message: "Internal server error" });
  }
});

app.get("/items", verifyToken, async (req: Request, res: Response) => {
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

app.post(
  "/item",
  verifyToken,
  upload.single("image"),
  async (req: Request, res: Response) => {
    try {
      const user = (req as any).user;
      const { name, category } = req.body;
      const file = req.file;

      if (!file || !name || !category) {
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
            date: "",
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

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
