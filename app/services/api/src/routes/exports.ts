import { Router } from "express";
import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { ExportsRepository } from "../repositories/exports";
import { config, isS3PathStyle } from "../config";

// Create a separate S3 client for pre-signed URLs using the public endpoint
function createPublicS3Client() {
  return new S3Client({
    region: config.AWS_REGION,
    endpoint: config.S3_PUBLIC_ENDPOINT_URL || config.S3_ENDPOINT_URL,
    forcePathStyle: isS3PathStyle()
  });
}

export function exportsRoutes(deps: { exportsRepo: ExportsRepository; s3: S3Client }) {
  const router = Router();
  const publicS3 = createPublicS3Client();

  router.get("/:exportId", async (req, res) => {
    const job = await deps.exportsRepo.getExport(req.params.exportId);
    if (!job) return res.status(404).json({ message: "Export not found" });

    let downloadUrl: string | undefined;
    if (job.status === "COMPLETED" && job.s3Key) {
      downloadUrl = await getSignedUrl(
        publicS3,
        new GetObjectCommand({
          Bucket: config.S3_BUCKET,
          Key: job.s3Key
        }),
        { expiresIn: 60 * 10 }
      );
    }

    res.json({ job, downloadUrl });
  });

  return router;
}
