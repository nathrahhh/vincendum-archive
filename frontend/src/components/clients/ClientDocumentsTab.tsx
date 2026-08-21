import { useEffect, useState } from "react";
import {
  fetchClientDocuments,
  getClientDocument,
} from "../../services/clientService";
import type { DocumentRecord } from "../../types";

type ClientDocumentsTabProps = {
  clientId: number;
};

function formatDateTime(value: string | undefined): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function ClientDocumentsTab({ clientId }: ClientDocumentsTabProps) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDocuments() {
      setIsLoading(true);
      setError(null);
      setDownloadError(null);
      setDocuments([]);

      try {
        const data = await fetchClientDocuments(clientId);
        if (!cancelled) {
          setDocuments(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load documents",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [clientId]);

  async function handleViewDownload(documentId: number) {
    setDownloadError(null);
    setDownloadingId(documentId);

    try {
      const response = await getClientDocument(clientId, documentId);
      if (!response.download_url) {
        throw new Error("No download URL was returned for this document");
      }
      window.open(response.download_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setDownloadError(
        err instanceof Error ? err.message : "Failed to open document",
      );
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <section>
      <h3 className="deal-result-panel__breaches-title">Documents</h3>

      {error ? <p className="dashboard-error">{error}</p> : null}
      {downloadError ? <p className="dashboard-error">{downloadError}</p> : null}

      {isLoading ? (
        <p className="clients-panel__hint">Loading documents…</p>
      ) : null}

      {!isLoading && !error && documents.length === 0 ? (
        <p className="clients-panel__hint">No documents uploaded.</p>
      ) : null}

      {!isLoading && documents.length > 0 ? (
        <div className="dashboard-table-wrap">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((document) => (
                <tr key={document.id}>
                  <td>{document.name}</td>
                  <td>{formatDateTime(document.created_at)}</td>
                  <td>
                    <button
                      type="button"
                      className="deal-form__submit"
                      disabled={downloadingId === document.id}
                      onClick={() => {
                        void handleViewDownload(document.id);
                      }}
                    >
                      {downloadingId === document.id
                        ? "Opening…"
                        : "View / Download"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
