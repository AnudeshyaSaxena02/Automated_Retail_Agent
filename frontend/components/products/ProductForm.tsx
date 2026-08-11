"use client";

// ============================================================
// components/products/ProductForm.tsx
//
// Form for creating a new product using react-hook-form and Zod.
// Maps to the ProductCreateRequest backend contract.
// ============================================================

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import type { ProductCreateRequest } from "@/types/contracts/products";

const formSchema = z.object({
  product_id: z.string().min(1, "Product ID is required").max(50),
  name: z.string().min(1, "Name is required").max(200),
  description: z.string().optional(),
  category: z.string().min(1, "Category is required").max(100),
  brand: z.string().optional(),
  price: z.number({ message: "Price must be a number" }).positive("Price must be greater than 0"),
  stock: z.number({ message: "Stock must be a number" }).min(0, "Stock cannot be negative"),
  tagsStr: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface ProductFormProps {
  onSubmit: (data: ProductCreateRequest) => void;
  isPending: boolean;
  onCancel: () => void;
}

export function ProductForm({ onSubmit, isPending, onCancel }: ProductFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      product_id: "",
      name: "",
      description: "",
      category: "",
      brand: "",
      price: 0,
      stock: 100,
      tagsStr: "",
    },
  });

  const onSubmitForm = (values: FormValues) => {
    // Convert comma-separated tags string into string[]
    const tags = values.tagsStr
      ? values.tagsStr.split(",").map((t) => t.trim()).filter(Boolean)
      : [];

    const requestData: ProductCreateRequest = {
      product_id: values.product_id,
      name: values.name,
      description: values.description || null,
      category: values.category,
      brand: values.brand || null,
      price: values.price,
      stock: values.stock,
      tags: tags.length > 0 ? tags : undefined,
    };

    onSubmit(requestData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="product_id">Product ID <span className="text-destructive">*</span></Label>
          <Input id="product_id" placeholder="e.g. PROD001" {...register("product_id")} disabled={isPending} />
          {errors.product_id && <p className="text-xs text-destructive">{errors.product_id.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="name">Name <span className="text-destructive">*</span></Label>
          <Input id="name" placeholder="e.g. Dell XPS 15" {...register("name")} disabled={isPending} />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="category">Category <span className="text-destructive">*</span></Label>
          <Input id="category" placeholder="e.g. Laptops" {...register("category")} disabled={isPending} />
          {errors.category && <p className="text-xs text-destructive">{errors.category.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="brand">Brand</Label>
          <Input id="brand" placeholder="e.g. Dell" {...register("brand")} disabled={isPending} />
          {errors.brand && <p className="text-xs text-destructive">{errors.brand.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="price">Price (₹) <span className="text-destructive">*</span></Label>
          <Input id="price" type="number" step="0.01" {...register("price", { valueAsNumber: true })} disabled={isPending} />
          {errors.price && <p className="text-xs text-destructive">{errors.price.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="stock">Initial Stock</Label>
          <Input id="stock" type="number" {...register("stock", { valueAsNumber: true })} disabled={isPending} />
          {errors.stock && <p className="text-xs text-destructive">{errors.stock.message}</p>}
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Input id="description" placeholder="Brief description of the product" {...register("description")} disabled={isPending} />
        {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="tagsStr">Tags (comma-separated)</Label>
        <Input id="tagsStr" placeholder="e.g. laptop, premium, computing" {...register("tagsStr")} disabled={isPending} />
        {errors.tagsStr && <p className="text-xs text-destructive">{errors.tagsStr.message}</p>}
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isPending}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
          {isPending ? "Creating..." : "Create Product"}
        </Button>
      </div>
    </form>
  );
}
