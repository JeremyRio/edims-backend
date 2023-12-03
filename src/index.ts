import express, { Request, Response } from "express";
import { User, LoginCredentials } from "./interface";
import bcrypt from "bcrypt";
import { PrismaClient } from "@prisma/client";
import { generateToken } from "./authentication";
import dotenv from "dotenv";

dotenv.config();

const app = express();

const port = process.env.port || 3000;
const prisma = new PrismaClient();

app.use(express.json());

app.get("/", (req, res) => {
  res.send("Hello, TypeScript Express!");
});

app.post("/register", async (req: Request, res: Response) => {
  const { email, username, password }: User = req.body;

  try {
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
    res.status(201).json({ user: userWithoutPassword });
  } catch (error) {
    res.status(400).json({ message: "Unable to register user" });
  }
});

app.post("/login", async (req: Request, res: Response) => {
  const { email, password }: LoginCredentials = req.body;

  try {
    const user = await prisma.user.findUnique({ where: { email } });

    if (user && bcrypt.compareSync(password, user.password)) {
      const token = generateToken(user.id);

      res.status(200).json({ message: "Login successful", token: token });
    } else {
      res.status(401).json({ message: "Invalid email or password" });
    }
  } catch (error) {
    res.status(500).json({ message: "Internal server error" });
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
