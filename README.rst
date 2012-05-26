Introduction
============

This product was created to help you remove nasty local persistent
utilities that won't go away and can destroy your instance when
you try to remove a product that registered one.

Features
--------

 - remove adapters
 - remove subscribers
 - remove provided interfaces
 - remove provided interfaces across the entire site
   - useful for removing collective.flowplayer

Just append '/@@fix-persistent-utilities' onto your plone site root
or the root of zope(for gsm) and browse through all your registered
utilities on your site and remove things at will.

By default, the tools prevents you from removing certain 
registrations; however, you can enter "expert mode" and remove 
whatever you want.




WARNING!!!
----------

You can really screw up things if you do this wrong so use with
extreme care and backup your instance before you use it.

I will not take responsibility if you misuse this tool...


Advice
------

Do not include this product as part of your normal set of
products. Only install this product on debug zope clients.

This product should allow you to remove things from products that are
no longer installed on the system; although, if you experience problems
removing things, make sure to add those eggs to the system again.

