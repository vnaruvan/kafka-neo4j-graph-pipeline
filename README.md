# Kafka → Neo4j Graph Pipeline

A reproducible Kubernetes pipeline demonstrating real-time data streaming from Kafka into Neo4j graph database using Kafka Connect with the Neo4j Sink Connector.

**Stack:** Kafka · Zookeeper · Neo4j · Kafka Connect · Kubernetes · Helm

---

## Quick Start

**Prerequisites:** Local Kubernetes cluster (KinD/Docker Desktop/minikube), `kubectl`, `helm`, Python 3.10+ (optional)

```bash
# Deploy entire pipeline
chmod +x start.sh
./start.sh
```

This creates the `graph-pipeline` namespace and deploys all components.

**Verify deployment:**
```bash
kubectl get pods -n graph-pipeline
kubectl get svc -n graph-pipeline
```

Expected: All pods `Running` with status `1/1`

---

## Architecture

### Components

| Component | Purpose |
|-----------|---------|
| **Zookeeper** | Kafka cluster coordination |
| **Kafka** | Event streaming platform |
| **Neo4j** | Graph database (deployed via Helm) |
| **Kafka Connect** | Integration runtime with Neo4j Sink Connector |

### Data Flow

```
Data Source → Kafka Topic → Kafka Connect → Neo4j Sink Connector → Neo4j Graph
```

---

## Accessing Services

### Neo4j Browser

**Port-forward:**
```bash
kubectl port-forward -n graph-pipeline svc/neo4j 7474:7474 7687:7687
```

**Access:** http://localhost:7474

**Credentials:**
- Username: `neo4j`
- Password: _(see `.env.example` for `NEO4J_PASSWORD`)_

### Kafka Connect REST API

**Port-forward:**
```bash
kubectl port-forward -n graph-pipeline svc/kafka-neo4j-connector 8083:8083
```

**Check connectors:**
```bash
# List all connectors
curl -s http://localhost:8083/connectors

# Check connector status
curl -s http://localhost:8083/connectors/Neo4jSinkConnectorJSONString/status
```

---

## Demo: NYC Taxi Dataset

This optional demo loads real taxi trip data to create a screenshotable graph visualization.

### Step 1: Generate Sample CSV

Download NYC TLC data (example: `yellow_tripdata_2022-03.parquet`) and create a sample:

```bash
python3 - <<'PY'
import pandas as pd

src = "yellow_tripdata_2022-03.parquet"
out = "yellow_tripdata_2022-03_sample.csv"

df = pd.read_parquet(src).head(20000)
df.to_csv(out, index=False)

print(f"Wrote: {out} | Rows: {len(df)}")
PY
```

### Step 2: Copy CSV to Neo4j Pod

```bash
kubectl cp -n graph-pipeline \
  yellow_tripdata_2022-03_sample.csv \
  neo4j-0:/var/lib/neo4j/import/yellow_tripdata_2022-03_sample.csv
```

**Verify:**
```bash
kubectl exec -n graph-pipeline neo4j-0 -- ls -lh /var/lib/neo4j/import | tail
```

### Step 3: Load Data into Neo4j

Open Neo4j Browser and run:

```cypher
LOAD CSV WITH HEADERS FROM "file:///yellow_tripdata_2022-03_sample.csv" AS row
WITH row
WHERE row.PULocationID IS NOT NULL AND row.DOLocationID IS NOT NULL
WITH row LIMIT 5000
MERGE (pu:Location {id: toInteger(row.PULocationID)})
MERGE (do:Location {id: toInteger(row.DOLocationID)})
CREATE (t:Trip {
  pickup: row.tpep_pickup_datetime,
  dropoff: row.tpep_dropoff_datetime
})
CREATE (t)-[:PICKUP_AT]->(pu)
CREATE (t)-[:DROPOFF_AT]->(do);
```

### Step 4: Verify and Visualize

**Check node counts:**
```cypher
MATCH (n) 
RETURN labels(n) AS labels, count(*) AS cnt 
ORDER BY cnt DESC;
```

**Graph visualization (perfect for screenshots):**
```cypher
MATCH (pu:Location)<-[:PICKUP_AT]-(t:Trip)-[:DROPOFF_AT]->(do:Location)
RETURN pu, t, do
LIMIT 50;
```

This creates a visual graph showing taxi trips connecting pickup and dropoff locations.

---

## Configuration

### Neo4j CSV Import Settings

CSV imports are enabled via Helm values (`helm/neo4j-values.yaml`):

```yaml
dbms.security.allow_csv_import_from_file_urls: true
server.directories.import: /var/lib/neo4j/import
```

These settings allow file-based imports for demo purposes.

---

## Troubleshooting

### Kafka Connect OOMKilled / CrashLoopBackOff

**Symptom:** Kafka Connect pod restarts repeatedly

**Cause:** Insufficient memory or CPU resources

**Fix:** Increase resource limits in deployment manifest or `start.sh`:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### LOAD CSV "Couldn't load the external resource"

**Symptom:** CSV import fails with file access error

**Cause:** File URL imports disabled or incorrect import directory

**Diagnosis:** Verify settings in Neo4j Browser:

```cypher
SHOW SETTINGS YIELD name, value
WHERE name IN [
  'dbms.security.allow_csv_import_from_file_urls',
  'server.directories.import',
  'dbms.directories.import'
]
RETURN name, value;
```

**Fix:** Ensure Helm values include:
- `dbms.security.allow_csv_import_from_file_urls=true`
- Import directory configured correctly

### No Pods Running

**Diagnosis:**
```bash
kubectl get events -n graph-pipeline --sort-by='.lastTimestamp'
kubectl describe pod <pod-name> -n graph-pipeline
```

**Common causes:**
- Image pull errors
- Insufficient cluster resources
- PVC binding issues (for Neo4j)

---

## Repository Structure

```
.
├── docker/
│   ├── Dockerfile           # Container image for Connect/loader
│   └── src/
│       ├── data_loader.py   # Data conversion utilities (optional)
│       └── interface.py     # Helper utilities (optional)
├── k8s/
│   ├── zookeeper-setup.yaml
│   ├── kafka-setup.yaml
│   └── kafka-neo4j-connector.yaml
├── helm/
│   └── neo4j-values.yaml    # Neo4j Helm configuration
├── start.sh                 # One-command deployment script
└── .env.example             # Environment variable template
```

---

## Cleanup

Remove all pipeline components:

```bash
kubectl delete namespace graph-pipeline
```

This removes Zookeeper, Kafka, Neo4j, Kafka Connect, and all associated resources.

---

## Use Cases

This pipeline demonstrates patterns useful for:
- **Real-time graph analytics** - Stream events into graph structures
- **Fraud detection** - Build relationship graphs from transaction streams
- **Recommendation engines** - Connect users, products, and interactions
- **Network analysis** - Model connections and dependencies
- **Knowledge graphs** - Build connected data from event streams

---

## Next Steps

### Extend the Pipeline

**Add custom connectors:**
```bash
# Example: add a source connector
kubectl apply -f k8s/custom-source-connector.yaml
```

**Scale Kafka brokers:**
```bash
kubectl scale deployment kafka -n graph-pipeline --replicas=3
```

**Enable Neo4j clustering:**
Modify `helm/neo4j-values.yaml` to configure multiple replicas

### Production Considerations

- **Security:** Enable authentication, TLS, and network policies
- **Persistence:** Configure PVCs with appropriate storage classes
- **Monitoring:** Add Prometheus metrics and Grafana dashboards
- **Resource limits:** Tune CPU/memory based on workload
- **Backup:** Implement Neo4j backup strategy

---
