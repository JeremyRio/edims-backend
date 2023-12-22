import express from "express";
import { Request, Response } from "express";
import { User, LoginCredentials } from "../interfaces/interface";
import { PrismaClient } from "@prisma/client";
import bcrypt from "bcrypt";
import { generateToken } from "../authentication/authentication";

const prisma = new PrismaClient();

const router = express.Router();

router.post("/register", async (req: Request, res: Response) => {
  try {
    const { email, username, password }: User = req.body;

    const existingUser = await prisma.user.findFirst({
      where: {
        email: email,
      },
    });

    if (existingUser) {
      return res.status(400).json({ message: "User already exists" });
    }

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
    const token = generateToken(userWithoutPassword);
    res.status(201).json({
      message: "Register successful",
      user: userWithoutPassword,
      token: token,
    });
  } catch (error) {
    res.status(500).json({ message: "Internal server error" });
  }
});

router.post("/login", async (req: Request, res: Response) => {
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

export default router;
