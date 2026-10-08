/**
 * ESTRUCTURA DEL CONTENIDO
 * Define qué campos debe tener cada ficha. Si una ficha tiene un campo mal
 * escrito o le falta uno obligatorio, Astro avisa al arrancar o al compilar.
 */
import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { conNombre } from "./config/site";

const servidores = defineCollection({
  // Una ficha por servidor. El nombre del fichero es el "slug" (aparece en la URL
  // y es la clave que usa el backend en servers.yaml).
  loader: glob({ pattern: "*.md", base: "./src/content/servidores" }),
  schema: z.object({
    nombre: z.string(),
    mapa: z.string(),
    modo: z.enum(["PvE", "PvP"]),
    resumen: z.string().max(160),
    imagen: z.string(), // ruta dentro de public/, p. ej. /img/servidores/the-island.jpg
    visible: z.boolean().default(true),
    destacado: z.boolean().default(false),
    orden: z.number().default(100),
    cluster: z.string().optional(),
    jugadoresMax: z.number().int().positive(),
    rates: z.object({
      xp: z.number(),
      doma: z.number(),
      recoleccion: z.number(),
      cria: z.number(),
    }),
    conexion: z.object({
      // Puede llevar {nombre}: se sustituye por el nombre del proyecto (site.ts)
      nombreEnBuscador: z.string().transform(conNombre),
      plataformas: z.array(z.enum(["PC", "Xbox", "PlayStation"])).default(["PC"]),
      contrasena: z.boolean().default(false),
    }),
    caracteristicas: z.array(z.string()).default([]),
    mods: z.array(z.object({ nombre: z.string(), id: z.number().optional() })).default([]),
    normas: z.array(z.string()).default(["generales"]),
  }),
});

const normas = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/normas" }),
  schema: z.object({
    titulo: z.string(),
    orden: z.number().default(100),
  }),
});

export const collections = { servidores, normas };
