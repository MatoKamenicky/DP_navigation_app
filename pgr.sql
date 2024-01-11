--select assign_vertex_id('data_marianka',  0.001, 'geom', 'gid');
--select pgr_createTopology('data_marianka',  0.001, the_geom:='geom');
ALTER TABLE public.data_marianka 
  ALTER COLUMN geom TYPE geometry(LineString,4326)
  USING ST_Force2D(geom);
  
SELECT  pgr_createTopology('roads_select',0.1,'geom');		










