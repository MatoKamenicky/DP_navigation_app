--select assign_vertex_id('data_marianka',  0.001, 'geom', 'gid');

set search_path to public

/*
alter table public.planet_osm_line add column "source" integer;
alter table public.planet_osm_line add column "target" integer;
select pgr_createTopology('public.planet_osm_line',  0.001, 'way', 'osm_id');
*/

select pgr_analyzegraph('public.planet_osm_line', 0.001,'way', 'osm_id');

select pgr_nodeNetwork('public.planet_osm_line', 0.001,'osm_id', 'way');

select pgr_createTopology('public.planet_osm_line_noded',  0.001, 'way', 'sub_id');

alter table planet_osm_line_noded add column 'cost' integer;
update planet_osm_line_noded set cost = 1;

alter table planet_osm_line add column "cost" integer;
update planet_osm_line set cost = 1;

ALTER TABLE planet_osm_line ADD COLUMN reverse_cost double precision;
UPDATE planet_osm_line SET reverse_cost = ST_length(planet_osm_line.way);
ALTER TABLE planet_osm_line_noded ADD COLUMN reverse_cost double precision;
UPDATE planet_osm_line_noded SET reverse_cost = ST_length(planet_osm_line_noded.way)

--Pokus djikstrov algoritmus
select * from pgr_dijkstra('select osm_id as id,source,target,reverse_cost as cost from public.planet_osm_line'
						   ,904847497,136987248,false);
						   
SELECT * FROM pgr_dijkstra(
    'SELECT id, source, target, cost FROM planet_osm_line_noded',
    source_node_id,
    target_node_id,
    directed := true/false
);

--Pridanie noveho stlpca s id
alter table planet_osm_line_vertices_pgr add column "id2" integer;
update planet_osm_line_vertices_pgr set id2 = row_number() OVER (ORDER BY your_ordering_column) - 1 + 1;; 

alter table planet_osm_line add column "id_new" integer;
update planet_osm_line set id_new = row_number();





--vykreslenie geometrie
select ST_transform(way,4326) from planet_osm_line


--Skuska s tabulkami osm_nodes a osm_edges
alter table osm_edges add column "source" integer;
alter table osm_edges add column "target" integer;
alter table osm_edges add column "id_new" integer;
update osm_edges set id_new = cast(osmid as INTEGER);


select pgr_createTopology('osm_edges',  0.001, 'geometry', 'osmid');
osm_edges
select * from pgr_dijkstra('select osm_id as id,source,target,reverse_cost as cost from osm_edges'
						   ,3,8,false);

--id ako serial
alter table osm_edges
drop column id_new;

alter table planet_osm_line
add column "id_new" serial;




