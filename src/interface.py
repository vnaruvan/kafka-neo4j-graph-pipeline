from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, pwd):
        print("connecting to db")
        self.dbdriver = GraphDatabase.driver(uri, auth=(user, pwd), encrypted=False)
        self.dbdriver.verify_connectivity()
        print("connected")

    def close(self):
        print("closing db")
        self.dbdriver.close()
        print("closed")

    def pagerank(self, max_iterations, weight_property):
        with self.dbdriver.session() as session:
            graphnm = "graph"
            ex = session.run(
                "CALL gds.graph.exists($g) YIELD exists RETURN exists", {"g": graphnm}
            ).single()[0]
            if ex:
                session.run("CALL gds.graph.drop($g) YIELD graphName RETURN graphName", {"g": graphnm})
            session.run(
                "CALL gds.graph.project($g,$nl,$rl,{relationshipProperties:$rprops})",
                {"g": graphnm, "nl": "Location", "rl": "TRIP", "rprops": ["distance", "fare"]},
            )

            print("run pr")
            use_wp = weight_property if weight_property in ("distance", "fare") else None
            cfg = {"maxIterations": max_iterations, "dampingFactor": 0.85}
            if use_wp:
                cfg["relationshipWeightProperty"] = use_wp
            qtext = (
                "CALL gds.pageRank.stream($g,$cfg) "
                "YIELD nodeId, score "
                "RETURN gds.util.asNode(nodeId).name AS locid, score "
                "ORDER BY score DESC"
            )
            resultlt = list(session.run(qtext, {"g": graphnm, "cfg": cfg}))
            if not resultlt:
                print("no pr")
                return [{'name': -1, 'score': 0.0}, {'name': -1, 'score': 0.0}]

            topnd, lownd = resultlt[0], resultlt[-1]
            out = []
            for nm, sc in ((topnd["locid"], topnd["score"]), (lownd["locid"], lownd["score"])):
                out.append({"name": int(nm), "score": float(sc)})
            print("pr done")
            return out

    def bfs(self, start_node, last_node):
        with self.dbdriver.session() as session:
            graphnm = "graph"
            ex = session.run(
                "CALL gds.graph.exists($g) YIELD exists RETURN exists", {"g": graphnm}
            ).single()[0]
            if ex:
                session.run("CALL gds.graph.drop($g) YIELD graphName RETURN graphName", {"g": graphnm})
            session.run("CALL gds.graph.project($g,$nl,$rl)", {"g": graphnm, "nl": "Location", "rl": "TRIP"})

            print("run bfs")
            startloc = start_node
            endloc = last_node
            ids = session.run(
                "MATCH (a:Location {name:$A}), (b:Location {name:$B}) "
                "RETURN id(a) AS a_id, id(b) AS b_id",
                {"A": startloc, "B": endloc},
            ).single()
            (src_id, dst_id) = (ids["a_id"], ids["b_id"]) if ids else (None, None)
            if src_id is None or dst_id is None:
                return [{'path': []}]

            qtext = (
                "CALL gds.bfs.stream($g,{sourceNode:$src,targetNodes:[$dst]}) "
                "YIELD nodeIds "
                "RETURN [nid IN nodeIds | gds.util.asNode(nid).name] AS locpt"
            )
            r = session.run(qtext, {"g": graphnm, "src": src_id, "dst": dst_id}).single()
            the_path = r["locpt"] if r and r["locpt"] is not None else []
            if not the_path:
                print("no bfs")
                return [{'path': []}]
            print("bfs ok")
            return [{'path': [{'name': int(n)} for n in the_path]}]

